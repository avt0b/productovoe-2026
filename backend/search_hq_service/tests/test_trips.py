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


def test_cancel_trip_notifies_registered_and_blocks_further_actions(client, leader_header, monkeypatch):
    import services.trip_service as trip_service_module

    calls = []
    monkeypatch.setattr(
        trip_service_module.notify_client, "notify_users", lambda **kw: calls.append(kw)
    )

    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"]).json()
    vol = auth_header(user_id="vol-a")
    client.post(f"/trips/{trip['id']}/registrations", headers=vol)

    other = auth_header(role="searcher")
    assert (
        client.post(f"/trips/{trip['id']}/cancel", headers=other, json={"reason": "дождь"}).status_code
        == 403
    )

    r = client.post(f"/trips/{trip['id']}/cancel", headers=leader_header, json={"reason": "дождь"})
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert r.json()["cancel_reason"] == "дождь"
    assert calls and calls[0]["user_ids"] == ["vol-a"]

    # повторная отмена — конфликт
    assert client.post(f"/trips/{trip['id']}/cancel", headers=leader_header).status_code == 409
    # на отменённый выезд нельзя записаться и нельзя его править
    assert client.post(f"/trips/{trip['id']}/registrations", headers=auth_header()).status_code == 409
    assert (
        client.patch(f"/trips/{trip['id']}", headers=leader_header, json={"title": "x"}).status_code
        == 409
    )


def test_trip_keeps_meeting_point(client, leader_header):
    """Место сбора выезда — своя точка, а не штаб отряда: отряд базируется в
    городе, а собираются у деревни, до которой ехать час."""
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"], lat=53.0781, lon=36.1203).json()
    assert (trip["lat"], trip["lon"]) == (53.0781, 36.1203)

    # Место уточнили позже — правится как остальные поля выезда.
    moved = client.patch(
        f"/trips/{trip['id']}", headers=leader_header, json={"lat": 53.08, "lon": 36.13}
    )
    assert moved.status_code == 200
    assert (moved.json()["lat"], moved.json()["lon"]) == (53.08, 36.13)

    # В списке координаты тоже есть — по ним выезд ставят на карту.
    listed = next(t for t in client.get("/trips").json() if t["id"] == trip["id"])
    assert (listed["lat"], listed["lon"]) == (53.08, 36.13)


def test_trip_without_meeting_point_is_fine(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"]).json()
    assert trip["lat"] is None and trip["lon"] is None


def test_trip_meeting_point_out_of_range_is_422(client, leader_header):
    squad = make_squad(client, leader_header)
    assert make_trip(client, leader_header, squad["id"], lat=91, lon=36.1).status_code == 422
