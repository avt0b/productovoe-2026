from datetime import UTC, datetime, timedelta

from conftest import auth_header

TODAY = datetime.now(UTC).date()
FUTURE = (TODAY + timedelta(days=14)).isoformat()


def make_squad(client, header):
    return client.post("/squads", headers=header, json={"name": "Высота", "region": "Орёл"}).json()


def make_trip(client, leader_header, squad_id, **over):
    body = {
        "title": "Раскопки у д. Семенково",
        "location": "д. Семенково",
        "starts_on": FUTURE,
        "capacity": 2,
        "checklist": "лопата, щуп, перчатки, регистрация на «Память народа»",
    }
    body.update(over)
    return client.post(f"/squads/{squad_id}/trips", headers=leader_header, json=body)


def test_create_trip_requires_manager(client, leader_header):
    squad = make_squad(client, leader_header)
    assert make_trip(client, auth_header(role="searcher"), squad["id"]).status_code == 403
    assert make_trip(client, leader_header, squad["id"]).status_code == 201


def test_registration_capacity_and_cancel(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"], capacity=2).json()

    a = auth_header(user_id="vol-a")
    b = auth_header(user_id="vol-b")
    c = auth_header(user_id="vol-c")

    assert client.post(f"/trips/{trip['id']}/registrations", headers=a).status_code == 201
    assert client.post(f"/trips/{trip['id']}/registrations", headers=b).status_code == 201
    # мест больше нет
    assert client.post(f"/trips/{trip['id']}/registrations", headers=c).status_code == 409

    # повторная регистрация того же волонтёра идемпотентна
    assert client.post(f"/trips/{trip['id']}/registrations", headers=a).status_code == 201

    # a отменяет — освобождается место для c
    assert client.delete(f"/trips/{trip['id']}/registrations/me", headers=a).status_code == 204
    assert client.post(f"/trips/{trip['id']}/registrations", headers=c).status_code == 201


def test_registration_awards_volunteer_achievement(client, leader_header, monkeypatch):
    import services.trip_service as trip_service_module

    calls = []
    monkeypatch.setattr(
        trip_service_module, "award_achievement", lambda **kw: calls.append(kw)
    )

    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"]).json()

    client.post(f"/trips/{trip['id']}/registrations", headers=auth_header(user_id="vol-a"))
    assert calls == [{"user_id": "vol-a", "code": "trip_volunteer"}]


def test_update_rejects_capacity_below_registered(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"], capacity=2).json()

    client.post(f"/trips/{trip['id']}/registrations", headers=auth_header(user_id="vol-a"))
    client.post(f"/trips/{trip['id']}/registrations", headers=auth_header(user_id="vol-b"))

    r = client.patch(f"/trips/{trip['id']}", headers=leader_header, json={"capacity": 1})
    assert r.status_code == 409

    ok = client.patch(f"/trips/{trip['id']}", headers=leader_header, json={"capacity": 2})
    assert ok.status_code == 200
    assert ok.json()["capacity"] == 2


def test_registrations_list_manager_only(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"]).json()
    client.post(f"/trips/{trip['id']}/registrations", headers=auth_header(user_id="vol-a"))

    assert (
        client.get(
            f"/trips/{trip['id']}/registrations", headers=auth_header(user_id="vol-a")
        ).status_code
        == 403
    )
    r = client.get(f"/trips/{trip['id']}/registrations", headers=leader_header)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_trips_feed_upcoming_only(client, leader_header):
    squad = make_squad(client, leader_header)
    past = (TODAY - timedelta(days=5)).isoformat()
    make_trip(client, leader_header, squad["id"], title="прошедший", starts_on=past)
    make_trip(client, leader_header, squad["id"], title="будущий")

    feed = client.get("/trips").json()
    assert [t["title"] for t in feed] == ["будущий"]
    all_ = client.get("/trips", params={"upcoming_only": False}).json()
    assert {t["title"] for t in all_} == {"прошедший", "будущий"}


def test_my_trips_lists_only_active_registrations(client, leader_header):
    squad = make_squad(client, leader_header)
    first = make_trip(client, leader_header, squad["id"], title="Разведка").json()
    second = make_trip(client, leader_header, squad["id"], title="Раскопки").json()
    past = make_trip(
        client, leader_header, squad["id"], title="Прошлый", starts_on=(TODAY - timedelta(days=3)).isoformat()
    ).json()

    me = auth_header(user_id="vol-me")
    for trip in (first, second, past):
        assert client.post(f"/trips/{trip['id']}/registrations", headers=me).status_code == 201
    assert client.delete(f"/trips/{second['id']}/registrations/me", headers=me).status_code == 204
    # Чужая запись в «мои выезды» не попадает.
    client.post(f"/trips/{second['id']}/registrations", headers=auth_header(user_id="vol-other"))

    upcoming = client.get("/trips/mine", headers=me)
    assert upcoming.status_code == 200
    assert [t["title"] for t in upcoming.json()] == ["Разведка"]

    everything = client.get("/trips/mine", headers=me, params={"upcoming_only": False}).json()
    assert {t["title"] for t in everything} == {"Разведка", "Прошлый"}

    assert client.get("/trips/mine").status_code == 401
