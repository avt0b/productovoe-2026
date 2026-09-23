from conftest import auth_header

from core.config import settings

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}


def award(client, user_id, code):
    return client.post(
        "/internal/achievements/award",
        headers=INTERNAL_HEADERS,
        json={"user_id": user_id, "code": code},
    )


def test_award_requires_internal_key(client):
    r = client.post("/internal/achievements/award", json={"user_id": "u1", "code": "donor"})
    assert r.status_code == 403


def test_award_creates_achievement_and_notification(client):
    r = award(client, "u1", "first_route_completed")
    assert r.status_code == 200
    assert r.json() == {"code": "first_route_completed", "awarded": True}

    mine = client.get("/achievements/me", headers=auth_header(user_id="u1")).json()
    assert [a["code"] for a in mine] == ["first_route_completed"]

    notifications = client.get("/notifications", headers=auth_header(user_id="u1")).json()
    assert len(notifications) == 1
    assert notifications[0]["kind"] == "achievement"
    assert notifications[0]["body"] == "Первый маршрут пройден"
    assert notifications[0]["payload"]["code"] == "first_route_completed"


def test_award_is_idempotent(client):
    award(client, "u1", "donor")
    r2 = award(client, "u1", "donor")
    assert r2.json() == {"code": "donor", "awarded": False}

    mine = client.get("/achievements/me", headers=auth_header(user_id="u1")).json()
    assert len(mine) == 1
    # второе уведомление не создалось.
    notifications = client.get("/notifications", headers=auth_header(user_id="u1")).json()
    assert len(notifications) == 1


def test_unknown_code_falls_back_to_code_as_title(client):
    award(client, "u1", "something_new")
    notifications = client.get("/notifications", headers=auth_header(user_id="u1")).json()
    assert notifications[0]["body"] == "something_new"


def test_achievements_are_per_user(client):
    award(client, "u1", "donor")
    award(client, "u2", "trip_volunteer")

    assert [a["code"] for a in client.get("/achievements/me", headers=auth_header(user_id="u1")).json()] == [
        "donor"
    ]
    assert [a["code"] for a in client.get("/achievements/me", headers=auth_header(user_id="u2")).json()] == [
        "trip_volunteer"
    ]


def test_my_achievements_requires_auth(client):
    assert client.get("/achievements/me").status_code in (401, 403)


def test_achievements_visible_on_own_and_public_profile(client):
    owner = auth_header(user_id="u1")
    # ленивое создание профиля, иначе GET /profiles/{id} будет 404.
    client.get("/profiles/me", headers=owner)

    award(client, "u1", "donor")
    award(client, "u1", "trip_volunteer")

    mine = client.get("/profiles/me", headers=owner).json()
    assert {a["code"] for a in mine["achievements"]} == {"donor", "trip_volunteer"}

    # виден и постороннему, зашедшему на чужой профиль по id.
    stranger_view = client.get("/profiles/u1", headers=auth_header(user_id="stranger")).json()
    assert {a["code"] for a in stranger_view["achievements"]} == {"donor", "trip_volunteer"}


def test_profile_without_achievements_has_empty_list(client):
    header = auth_header(user_id="u2")
    profile = client.get("/profiles/me", headers=header).json()
    assert profile["achievements"] == []
