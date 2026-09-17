from datetime import UTC, datetime, timedelta

from conftest import auth_header

from core.config import settings

INTERNAL_HEADER = {"X-Internal-Key": settings.internal_api_key}

TODAY = datetime.now(UTC).date()
FUTURE = (TODAY + timedelta(days=14)).isoformat()


def make_squad(client, header, **over):
    body = {"name": "Высота", "region": "Орёл"}
    body.update(over)
    return client.post("/squads", headers=header, json=body).json()


def make_need(client, header, squad_id, **over):
    body = {"kind": "funds", "title": "ГСМ на выезд", "target_amount": 1000}
    body.update(over)
    return client.post(f"/squads/{squad_id}/needs", headers=header, json=body).json()


def make_trip(client, header, squad_id, **over):
    body = {
        "title": "Раскопки у д. Семенково",
        "location": "д. Семенково",
        "starts_on": FUTURE,
        "capacity": 2,
        "checklist": "лопата, щуп, перчатки",
    }
    body.update(over)
    return client.post(f"/squads/{squad_id}/trips", headers=header, json=body).json()


# --- проверка ключа ---


def test_stats_requires_internal_key(client):
    assert client.get("/internal/stats").status_code == 403


def test_stats_rejects_wrong_key(client):
    r = client.get("/internal/stats", headers={"X-Internal-Key": "wrong-key"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_list_squads_requires_internal_key(client):
    assert client.get("/internal/squads").status_code == 403


def test_list_needs_requires_internal_key(client):
    assert client.get("/internal/needs").status_code == 403


def test_list_trips_requires_internal_key(client):
    assert client.get("/internal/trips").status_code == 403


def test_close_need_requires_internal_key(client, leader_header):
    squad = make_squad(client, leader_header)
    need = make_need(client, leader_header, squad["id"])
    r = client.post(f"/internal/needs/{need['id']}/close")
    assert r.status_code == 403


# --- /internal/stats ---


def test_stats_shape(client, leader_header):
    squad = make_squad(client, leader_header)

    funds_need = make_need(
        client, leader_header, squad["id"], kind="funds", title="ГСМ", target_amount=1000
    )
    client.post(
        f"/needs/{funds_need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 400, "comment": "на удачу"},
    )
    make_need(
        client,
        leader_header,
        squad["id"],
        kind="volunteers",
        title="Нужны землекопы",
        target_amount=5,
    )

    trip = make_trip(client, leader_header, squad["id"], capacity=2)
    client.post(f"/trips/{trip['id']}/registrations", headers=auth_header(user_id="vol-a"))

    client.post(
        "/excursions",
        headers=auth_header(role="local_historian", user_id="guide-1"),
        json={
            "title": "Экскурсия к мемориалу",
            "lat": 52.9,
            "lon": 36.0,
            "starts_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
    )

    r = client.get("/internal/stats", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "search_hq_service"
    assert data["squads_total"] == 1
    assert data["needs_total"] == 2
    assert data["needs_open"] == 2
    assert data["needs_by_kind"]["funds"] == 1
    assert data["needs_by_kind"]["volunteers"] == 1
    assert data["funds_target"] == 1000
    assert data["funds_collected"] == 400
    assert data["funds_progress"] == 0.4
    assert data["donations_count"] == 1
    assert data["donations_7d"] == 1
    assert data["volunteers_needed_open"] == 5
    assert data["trips_total"] == 1
    assert data["trips_upcoming"] == 1
    assert data["registrations_active"] == 1
    assert data["excursions_total"] == 1
    assert data["excursions_active"] == 1
    assert data["excursion_check_ins"] == 0


def test_stats_need_auto_closes_when_target_reached(client, leader_header):
    squad = make_squad(client, leader_header)
    need = make_need(
        client, leader_header, squad["id"], kind="funds", title="ГСМ", target_amount=100
    )
    client.post(
        f"/needs/{need['id']}/donations",
        headers=auth_header(user_id="donor-1"),
        json={"amount": 100},
    )

    r = client.get("/internal/stats", headers=INTERNAL_HEADER)
    data = r.json()
    assert data["needs_open"] == 0
    assert data["funds_progress"] == 1.0


# --- /internal/squads ---


def test_list_squads_shape_and_query(client, leader_header):
    squad = make_squad(client, leader_header, name="Высота", region="Орёл")
    make_squad(client, auth_header(role="searcher", user_id="other-leader"), name="Рубеж", region="Курск")

    r = client.get("/internal/squads", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert data["limit"] == 50
    assert data["offset"] == 0

    r = client.get("/internal/squads", headers=INTERNAL_HEADER, params={"query": "Высота"})
    assert [x["id"] for x in r.json()["items"]] == [squad["id"]]


# --- /internal/needs ---


def test_list_needs_filters(client, leader_header):
    squad = make_squad(client, leader_header)
    other_squad = make_squad(client, auth_header(role="searcher", user_id="other-leader"))
    funds_need = make_need(client, leader_header, squad["id"], kind="funds")
    vol_need = make_need(client, leader_header, squad["id"], kind="volunteers", target_amount=3)
    make_need(client, auth_header(role="searcher", user_id="other-leader"), other_squad["id"])

    r = client.get("/internal/needs", headers=INTERNAL_HEADER, params={"squad_id": squad["id"]})
    assert {x["id"] for x in r.json()["items"]} == {funds_need["id"], vol_need["id"]}

    r = client.get("/internal/needs", headers=INTERNAL_HEADER, params={"kind": "volunteers"})
    assert [x["id"] for x in r.json()["items"]] == [vol_need["id"]]

    client.post(f"/internal/needs/{funds_need['id']}/close", headers=INTERNAL_HEADER)
    r = client.get("/internal/needs", headers=INTERNAL_HEADER, params={"status": "closed"})
    assert [x["id"] for x in r.json()["items"]] == [funds_need["id"]]


# --- /internal/trips ---


def test_list_trips_filters(client, leader_header):
    squad = make_squad(client, leader_header)
    past = (TODAY - timedelta(days=5)).isoformat()
    past_trip = make_trip(client, leader_header, squad["id"], title="прошедший", starts_on=past)
    future_trip = make_trip(client, leader_header, squad["id"], title="будущий")

    r = client.get("/internal/trips", headers=INTERNAL_HEADER)
    assert r.status_code == 200
    assert {x["id"] for x in r.json()["items"]} == {past_trip["id"], future_trip["id"]}

    r = client.get("/internal/trips", headers=INTERNAL_HEADER, params={"upcoming_only": "true"})
    assert [x["id"] for x in r.json()["items"]] == [future_trip["id"]]

    r = client.get("/internal/trips", headers=INTERNAL_HEADER, params={"squad_id": squad["id"]})
    assert {x["id"] for x in r.json()["items"]} == {past_trip["id"], future_trip["id"]}


# --- мутации через internal_actor ---


def test_internal_close_need_bypasses_permissions(client, leader_header):
    squad = make_squad(client, leader_header)
    need = make_need(client, leader_header, squad["id"])

    # обычный посторонний не может закрыть чужую потребность
    assert client.post(
        f"/needs/{need['id']}/close", headers=auth_header(role="searcher", user_id="stranger")
    ).status_code == 403

    r = client.post(
        f"/internal/needs/{need['id']}/close",
        headers={**INTERNAL_HEADER, "X-Actor-Id": "admin-1"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "closed"


def test_internal_close_need_missing_404(client):
    r = client.post(
        "/internal/needs/does-not-exist/close",
        headers=INTERNAL_HEADER,
    )
    assert r.status_code == 404
