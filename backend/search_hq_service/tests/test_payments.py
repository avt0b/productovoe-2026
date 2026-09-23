import pytest
from conftest import auth_header

import services.need_service as need_service_module


class FakeGateway:
    """Подменяет ЮKassa в тестах: без сети, с управляемым статусом платежа."""

    def __init__(self):
        self.created: list[dict] = []
        self.next_payment_id = "pay_1"
        self.remote_status = "pending"

    def create_payment(self, *, amount_rub, description, return_url, metadata):
        self.created.append(
            {
                "amount_rub": amount_rub,
                "description": description,
                "return_url": return_url,
                "metadata": metadata,
            }
        )
        return {
            "id": self.next_payment_id,
            "status": "pending",
            "confirmation": {
                "type": "redirect",
                "confirmation_url": f"https://yookassa.ru/pay/{self.next_payment_id}",
            },
        }

    def get_payment(self, payment_id):
        return {"id": payment_id, "status": self.remote_status}


@pytest.fixture()
def fake_gateway(monkeypatch):
    gateway = FakeGateway()
    monkeypatch.setattr(need_service_module, "get_gateway", lambda: gateway)
    return gateway


def make_squad_and_need(client, header, *, target=None):
    squad = client.post(
        "/squads", headers=header, json={"name": "Отряд «Высота»", "region": "Орёл"}
    ).json()
    payload = {"kind": "funds", "title": "Экипировать отряд"}
    if target is not None:
        payload["target_amount"] = target
    need = client.post(f"/squads/{squad['id']}/needs", headers=header, json=payload).json()
    return need


def test_donation_with_gateway_is_pending_and_not_credited_yet(
    client, leader_header, fake_gateway
):
    need = make_squad_and_need(client, leader_header, target=1000)

    r = client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 500, "comment": "на бензин"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["confirmation_url"] == "https://yookassa.ru/pay/pay_1"

    # Пока ЮKassa не подтвердила — need не пополняется, взнос не в публичной ленте.
    assert client.get(f"/needs/{need['id']}").json()["collected_amount"] == 0
    assert client.get(f"/needs/{need['id']}/donations").json() == []

    assert fake_gateway.created[0]["amount_rub"] == 500
    assert fake_gateway.created[0]["metadata"] == {"need_id": need["id"], "donor_id": "donor-1"}


def test_webhook_confirms_payment_and_credits_need(client, leader_header, fake_gateway):
    need = make_squad_and_need(client, leader_header, target=1000)
    client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 500},
    )

    fake_gateway.remote_status = "succeeded"
    webhook = client.post(
        "/payments/yookassa/webhook",
        json={"type": "notification", "event": "payment.succeeded", "object": {"id": "pay_1"}},
    )
    assert webhook.status_code == 200

    updated = client.get(f"/needs/{need['id']}").json()
    assert updated["collected_amount"] == 500

    feed = client.get(f"/needs/{need['id']}/donations").json()
    assert [d["amount"] for d in feed] == [500]


def test_webhook_reaches_target_and_closes_need(client, leader_header, fake_gateway):
    need = make_squad_and_need(client, leader_header, target=500)
    client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 500},
    )

    fake_gateway.remote_status = "succeeded"
    client.post("/payments/yookassa/webhook", json={"object": {"id": "pay_1"}})

    assert client.get(f"/needs/{need['id']}").json()["status"] == "closed"


def test_webhook_cancels_payment_without_crediting(client, leader_header, fake_gateway):
    need = make_squad_and_need(client, leader_header, target=1000)
    client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 500},
    )

    fake_gateway.remote_status = "canceled"
    client.post("/payments/yookassa/webhook", json={"object": {"id": "pay_1"}})

    assert client.get(f"/needs/{need['id']}").json()["collected_amount"] == 0
    assert client.get(f"/needs/{need['id']}/donations").json() == []


def test_webhook_ignores_unknown_payment_id(client, leader_header, fake_gateway):
    make_squad_and_need(client, leader_header)
    webhook = client.post("/payments/yookassa/webhook", json={"object": {"id": "unknown"}})
    assert webhook.status_code == 200


def test_webhook_is_idempotent_once_succeeded(client, leader_header, fake_gateway):
    need = make_squad_and_need(client, leader_header, target=1000)
    client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 500},
    )
    fake_gateway.remote_status = "succeeded"
    client.post("/payments/yookassa/webhook", json={"object": {"id": "pay_1"}})
    # Повторный вебхук (ЮKassa шлёт с ретраями) не должен зачислить донат дважды.
    client.post("/payments/yookassa/webhook", json={"object": {"id": "pay_1"}})

    assert client.get(f"/needs/{need['id']}").json()["collected_amount"] == 500
