from datetime import UTC, datetime, timedelta

from conftest import auth_header

TODAY = datetime.now(UTC).date()
FUTURE = (TODAY + timedelta(days=14)).isoformat()

SITE = {"lat": 52.967986, "lon": 36.078488}


def make_squad(client, header):
    return client.post("/squads", headers=header, json={"name": "Высота", "region": "Орёл"}).json()


def make_trip(client, leader_header, squad_id, **over):
    body = {
        "title": "Раскопки у д. Семенково",
        "location": "д. Семенково",
        "starts_on": FUTURE,
        "capacity": 2,
    }
    body.update(over)
    return client.post(f"/squads/{squad_id}/trips", headers=leader_header, json=body).json()


def make_excursion(client, header, **over):
    body = {
        "title": "Тропа памяти: площадь Мира",
        "place_name": "Площадь Мира, Орёл",
        "starts_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "capacity": 2,
        **SITE,
    }
    body.update(over)
    return client.post("/excursions", headers=header, json=body).json()


# --- чат выезда ---


def test_trip_chat_requires_membership(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    outsider = auth_header(user_id="outsider")

    assert (
        client.post(f"/trips/{trip['id']}/messages", headers=outsider, json={"body": "Привет"}).status_code
        == 403
    )
    assert client.get(f"/trips/{trip['id']}/messages", headers=outsider).status_code == 403


def test_trip_chat_leader_and_registered_volunteer(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    volunteer = auth_header(user_id="vol-a")

    client.post(f"/trips/{trip['id']}/registrations", headers=volunteer)

    r = client.post(f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": "Сбор в 8:00"})
    assert r.status_code == 201
    assert r.json()["author_id"] == "leader-1"

    r2 = client.post(f"/trips/{trip['id']}/messages", headers=volunteer, json={"body": "Буду!"})
    assert r2.status_code == 201

    feed = client.get(f"/trips/{trip['id']}/messages", headers=volunteer).json()
    assert [m["body"] for m in feed] == ["Сбор в 8:00", "Буду!"]


def test_trip_chat_closed_after_cancelling_registration(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    volunteer = auth_header(user_id="vol-a")

    client.post(f"/trips/{trip['id']}/registrations", headers=volunteer)
    assert client.get(f"/trips/{trip['id']}/messages", headers=volunteer).status_code == 200

    client.delete(f"/trips/{trip['id']}/registrations/me", headers=volunteer)
    assert client.get(f"/trips/{trip['id']}/messages", headers=volunteer).status_code == 403


def test_trip_chat_moderator_access(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])
    moderator = auth_header(role="moderator")

    r = client.post(f"/trips/{trip['id']}/messages", headers=moderator, json={"body": "Проверка"})
    assert r.status_code == 201


def test_trip_chat_unknown_trip_404(client, leader_header):
    r = client.get("/trips/does-not-exist/messages", headers=leader_header)
    assert r.status_code == 404


# --- чат экскурсии ---


def test_excursion_chat_requires_membership(client):
    guide = auth_header(user_id="guide-1", role="local_historian")
    excursion = make_excursion(client, guide)
    outsider = auth_header(user_id="outsider")

    assert (
        client.post(
            f"/excursions/{excursion['id']}/messages", headers=outsider, json={"body": "Привет"}
        ).status_code
        == 403
    )


def test_excursion_chat_guide_and_registered_visitor(client):
    guide = auth_header(user_id="guide-1", role="local_historian")
    visitor = auth_header(user_id="visitor-1")
    excursion = make_excursion(client, guide)

    client.post(f"/excursions/{excursion['id']}/registrations", headers=visitor)

    r = client.post(
        f"/excursions/{excursion['id']}/messages", headers=guide, json={"body": "Встречаемся у фонтана"}
    )
    assert r.status_code == 201

    feed = client.get(f"/excursions/{excursion['id']}/messages", headers=visitor).json()
    assert feed[0]["body"] == "Встречаемся у фонтана"


# --- модерация ---


def test_profanity_is_rejected(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])

    r = client.post(f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": "он мудак"})
    assert r.status_code == 422
    assert r.json()["detail"] == "Соблюдайте правила нашего сообщества"

    feed = client.get(f"/trips/{trip['id']}/messages", headers=leader_header).json()
    assert feed == []


def test_configured_extra_word_is_rejected(client, leader_header, monkeypatch):
    from core.config import settings

    monkeypatch.setattr(settings, "chat_banned_words", "тестзапрет")
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])

    r = client.post(
        f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": "тут ТестЗапрет есть"}
    )
    assert r.status_code == 422


def test_clean_message_passes(client, leader_header):
    squad = make_squad(client, leader_header)
    trip = make_trip(client, leader_header, squad["id"])

    r = client.post(f"/trips/{trip['id']}/messages", headers=leader_header, json={"body": "Едем в 8"})
    assert r.status_code == 201
