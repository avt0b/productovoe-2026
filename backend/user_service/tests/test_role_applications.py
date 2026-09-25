"""POST /role-applications (заявка на роль) + /internal/role-applications/* (решение админа)."""

import uuid

import pytest
from conftest import auth_header

import services.role_application_service as role_application_service_module
from core.config import settings
from core.exceptions import ServiceUnavailable

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}


def submit(client, header, **over):
    body = {"requested_role": "searcher", "full_name": "Иван Иванов", "contact": "@ivan"}
    body.update(over)
    return client.post("/role-applications", headers=header, json=body)


@pytest.fixture(autouse=True)
def no_real_auth_calls(monkeypatch):
    """По умолчанию approve() не должен реально стучаться в auth_service —
    тесты, которым важен сам факт вызова, подменяют его сами."""
    monkeypatch.setattr(role_application_service_module.auth_client, "set_role", lambda **kw: None)


def test_submit_is_pending(client):
    r = submit(client, auth_header(user_id="u1"))
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    assert body["requested_role"] == "searcher"
    assert body["user_id"] == "u1"


def test_submit_duplicate_pending_conflicts(client):
    header = auth_header(user_id="u1")
    submit(client, header)
    r = submit(client, header)
    assert r.status_code == 409


def test_submit_already_has_role_conflicts(client):
    r = submit(client, auth_header(user_id="u1", role="searcher"))
    assert r.status_code == 409


def test_submit_root_conflicts(client):
    r = submit(client, auth_header(user_id="u1", is_root=True))
    assert r.status_code == 409


def test_list_mine_only_own(client):
    submit(client, auth_header(user_id="u1"))
    submit(client, auth_header(user_id="u2"), requested_role="local_historian")

    mine = client.get("/role-applications/mine", headers=auth_header(user_id="u1")).json()
    assert len(mine) == 1
    assert mine[0]["requested_role"] == "searcher"


def test_internal_requires_key(client):
    assert client.get("/internal/role-applications").status_code == 403
    assert (
        client.post(
            f"/internal/role-applications/{uuid.uuid4()}/approve", json={}
        ).status_code
        == 403
    )


def test_internal_list_defaults_to_pending(client):
    submit(client, auth_header(user_id="u1"))
    r = client.get("/internal/role-applications", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_approve_calls_auth_client_and_verifies_profile(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        role_application_service_module.auth_client,
        "set_role",
        lambda **kw: calls.append(kw),
    )
    header = auth_header(user_id="u1")
    client.get("/profiles/me", headers=header)  # создать профиль лениво
    app_id = submit(client, header).json()["id"]

    r = client.post(
        f"/internal/role-applications/{app_id}/approve",
        headers=INTERNAL_HEADERS,
        json={"note": "проверено"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved"
    assert body["review_note"] == "проверено"
    assert calls == [{"user_id": "u1", "role": "searcher"}]

    profile = client.get("/profiles/u1", headers=header).json()
    assert profile["is_verified"] is True


def test_reject_does_not_call_auth_client(client, monkeypatch):
    calls = []
    monkeypatch.setattr(
        role_application_service_module.auth_client,
        "set_role",
        lambda **kw: calls.append(kw),
    )
    header = auth_header(user_id="u1")
    app_id = submit(client, header).json()["id"]
    r = client.post(
        f"/internal/role-applications/{app_id}/reject",
        headers=INTERNAL_HEADERS,
        json={"note": "недостаточно доказательств"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    assert calls == []


def test_decide_twice_conflicts(client):
    header = auth_header(user_id="u1")
    app_id = submit(client, header).json()["id"]
    client.post(f"/internal/role-applications/{app_id}/reject", headers=INTERNAL_HEADERS, json={})
    r = client.post(
        f"/internal/role-applications/{app_id}/approve", headers=INTERNAL_HEADERS, json={}
    )
    assert r.status_code == 409


def test_approve_propagates_auth_client_failure(client, monkeypatch):
    def _fail(**kw):
        raise ServiceUnavailable("auth_service недоступен")

    monkeypatch.setattr(role_application_service_module.auth_client, "set_role", _fail)

    header = auth_header(user_id="u1")
    app_id = submit(client, header).json()["id"]
    r = client.post(
        f"/internal/role-applications/{app_id}/approve", headers=INTERNAL_HEADERS, json={}
    )
    assert r.status_code == 503


def test_submit_second_role_while_pending_conflicts(client):
    """Две заявки в очереди — это два одобрения подряд, из которых второе молча
    стирает первое: роль-то одна."""
    header = auth_header(user_id="u1")
    assert submit(client, header, requested_role="searcher").status_code == 201

    r = submit(client, header, requested_role="local_historian")
    assert r.status_code == 409
    assert "поисковик" in r.json()["detail"]

    # Очередь админа видит ровно одну заявку этого человека.
    queue = client.get("/internal/role-applications", headers=INTERNAL_HEADERS).json()["items"]
    assert [a["requested_role"] for a in queue if a["user_id"] == "u1"] == ["searcher"]


def test_submit_другая_роль_после_решения_разрешена(client):
    header = auth_header(user_id="u1")
    app_id = submit(client, header, requested_role="searcher").json()["id"]
    client.post(f"/internal/role-applications/{app_id}/reject", headers=INTERNAL_HEADERS, json={})

    # Отказали — можно просить другое: очередь свободна.
    assert submit(client, header, requested_role="local_historian").status_code == 201


def test_approve_records_previous_role(client):
    """Одобрение заменяет роль — какую именно, видно и админу, и человеку."""
    header = auth_header(user_id="u1")
    client.get("/profiles/me", headers=header)  # создать профиль лениво
    first = submit(client, header, requested_role="searcher").json()["id"]
    client.post(f"/internal/role-applications/{first}/approve", headers=INTERNAL_HEADERS, json={})

    # Человек уже поисковик — просит краеведа; заявку подаёт уже с новой ролью.
    searcher_header = auth_header(user_id="u1", role="searcher")
    second = submit(client, searcher_header, requested_role="local_historian").json()["id"]
    body = client.post(
        f"/internal/role-applications/{second}/approve", headers=INTERNAL_HEADERS, json={}
    ).json()

    assert body["status"] == "approved"
    assert body["previous_role"] == "searcher"
    # У первой заявки прежняя роль — «семья», с которой человек и начинал.
    mine = {a["id"]: a for a in client.get("/role-applications/mine", headers=searcher_header).json()}
    assert mine[first]["previous_role"] == "family"
