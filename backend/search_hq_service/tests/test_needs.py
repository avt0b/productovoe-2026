from conftest import auth_header


def make_squad(client, header):
    return client.post(
        "/squads", headers=header, json={"name": "Отряд «Высота»", "region": "Орёл"}
    ).json()


def test_create_need_requires_squad_manager(client, leader_header):
    squad = make_squad(client, leader_header)
    payload = {"kind": "funds", "title": "Экипировать отряд", "target_amount": 50000}

    assert (
        client.post(
            f"/squads/{squad['id']}/needs", headers=auth_header(role="searcher"), json=payload
        ).status_code
        == 403
    )

    r = client.post(f"/squads/{squad['id']}/needs", headers=leader_header, json=payload)
    assert r.status_code == 201
    assert r.json()["collected_amount"] == 0
    assert r.json()["status"] == "open"


def test_donation_flow_and_autoclose(client, leader_header):
    squad = make_squad(client, leader_header)
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "funds", "title": "Поднять бойца", "target_amount": 15000},
    ).json()

    r1 = client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(role="family"),
        json={"amount": 5000, "comment": "от нашего класса"},
    )
    assert r1.status_code == 201
    assert client.get(f"/needs/{need['id']}").json()["collected_amount"] == 5000

    # добиваем до цели — сбор автозакрывается
    client.post(f"/needs/{need['id']}/donations", headers=auth_header(), json={"amount": 10000})
    closed = client.get(f"/needs/{need['id']}").json()
    assert closed["collected_amount"] == 15000
    assert closed["status"] == "closed"

    # в закрытый сбор донат не проходит
    assert (
        client.post(
            f"/needs/{need['id']}/donations", headers=auth_header(), json={"amount": 100}
        ).status_code
        == 409
    )


def test_donation_awards_donor_achievement(client, leader_header, monkeypatch):
    import services.need_service as need_service_module

    calls = []
    monkeypatch.setattr(
        need_service_module, "award_achievement", lambda **kw: calls.append(kw)
    )

    squad = make_squad(client, leader_header)
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "funds", "title": "Экипировать отряд", "target_amount": 15000},
    ).json()

    client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 1000},
    )
    assert calls == [{"user_id": "donor-1", "code": "donor"}]


def test_public_donation_feed_hides_donor(client, leader_header):
    squad = make_squad(client, leader_header)
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "funds", "title": "ГСМ на выезд", "target_amount": 1000},
    ).json()

    own = client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 300, "comment": "на бензин"},
    )
    # Сам жертвователь свой взнос видит полностью.
    assert own.json()["donor_id"] == "donor-1"

    feed = client.get(f"/needs/{need['id']}/donations").json()
    assert [(d["amount"], d["comment"]) for d in feed] == [(300, "на бензин")]
    assert "donor_id" not in feed[0]


def test_donation_rejected_for_non_funds_need(client, leader_header):
    squad = make_squad(client, leader_header)
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "volunteers", "title": "5 землекопов", "target_amount": 5},
    ).json()
    assert (
        client.post(
            f"/needs/{need['id']}/donations", headers=auth_header(), json={"amount": 100}
        ).status_code
        == 409
    )


def test_needs_feed_defaults_to_open(client, leader_header):
    squad = make_squad(client, leader_header)
    n1 = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "funds", "title": "ГСМ"},
    ).json()
    client.post(f"/needs/{n1['id']}/close", headers=leader_header)
    client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "equipment", "title": "Щупы"},
    )
    open_feed = client.get("/needs").json()
    assert [n["title"] for n in open_feed] == ["Щупы"]


def test_delete_need_requires_manager(client, leader_header):
    squad = make_squad(client, leader_header)
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "equipment", "title": "Щупы по ошибке"},
    ).json()

    assert (
        client.delete(f"/needs/{need['id']}", headers=auth_header(role="searcher")).status_code == 403
    )
    assert client.delete(f"/needs/{need['id']}", headers=leader_header).status_code == 204
    assert client.get(f"/needs/{need['id']}").status_code == 404


def test_delete_need_blocked_after_donation(client, leader_header):
    squad = make_squad(client, leader_header)
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "funds", "title": "ГСМ", "target_amount": 100000},
    ).json()
    client.post(f"/needs/{need['id']}/donations", headers=auth_header(), json={"amount": 500})

    r = client.delete(f"/needs/{need['id']}", headers=leader_header)
    assert r.status_code == 409
    # сбор остаётся — можно только закрыть
    assert client.get(f"/needs/{need['id']}").status_code == 200
