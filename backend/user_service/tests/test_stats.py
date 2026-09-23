from conftest import auth_header

from core.config import settings

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}


def increment(client, user_id, metric):
    return client.post(
        "/internal/stats/increment",
        headers=INTERNAL_HEADERS,
        json={"user_id": user_id, "metric": metric},
    )


def test_increment_requires_internal_key(client):
    r = client.post("/internal/stats/increment", json={"user_id": "u1", "metric": "finds_count"})
    assert r.status_code == 403


def test_increment_creates_and_accumulates(client):
    r = increment(client, "u1", "routes_completed")
    assert r.status_code == 200
    assert r.json() == {"metric": "routes_completed", "value": 1}

    r2 = increment(client, "u1", "routes_completed")
    assert r2.json() == {"metric": "routes_completed", "value": 2}


def test_increment_not_idempotent_unlike_achievements(client):
    increment(client, "u1", "finds_count")
    increment(client, "u1", "finds_count")
    increment(client, "u1", "finds_count")

    header = auth_header(user_id="u1")
    profile = client.get("/profiles/me", headers=header).json()
    assert profile["finds_count"] == 3


def test_stats_are_per_user(client):
    increment(client, "u1", "excursions_completed")
    increment(client, "u2", "excursions_completed")
    increment(client, "u2", "excursions_completed")

    p1 = client.get("/profiles/me", headers=auth_header(user_id="u1")).json()
    p2 = client.get("/profiles/me", headers=auth_header(user_id="u2")).json()
    assert p1["excursions_completed"] == 1
    assert p2["excursions_completed"] == 2


def test_stats_visible_on_own_and_public_profile(client):
    owner = auth_header(user_id="u1")
    client.get("/profiles/me", headers=owner)  # ленивое создание профиля

    increment(client, "u1", "routes_completed")
    increment(client, "u1", "excursions_completed")
    increment(client, "u1", "finds_count")
    increment(client, "u1", "finds_count")

    mine = client.get("/profiles/me", headers=owner).json()
    assert mine["routes_completed"] == 1
    assert mine["excursions_completed"] == 1
    assert mine["finds_count"] == 2

    stranger_view = client.get("/profiles/u1", headers=auth_header(user_id="stranger")).json()
    assert stranger_view["routes_completed"] == 1
    assert stranger_view["finds_count"] == 2


def test_profile_without_stats_defaults_to_zero(client):
    header = auth_header(user_id="u2")
    profile = client.get("/profiles/me", headers=header).json()
    assert profile["routes_completed"] == 0
    assert profile["excursions_completed"] == 0
    assert profile["finds_count"] == 0


def test_unknown_metric_does_not_leak_into_named_fields(client):
    """Свободная строка metric — как и code у ачивок — но ProfileOut отдаёт
    только три конкретных числа, остальное копится, но наружу не лезет."""
    increment(client, "u1", "something_unexpected")
    profile = client.get("/profiles/me", headers=auth_header(user_id="u1")).json()
    assert profile["routes_completed"] == 0
    assert profile["excursions_completed"] == 0
    assert profile["finds_count"] == 0
