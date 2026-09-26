"""Тесты служебной плоскости /internal/* (используется admin_service)."""

import uuid

from conftest import auth_header

from core.config import settings

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}
WRONG_HEADERS = {"X-Internal-Key": "not-the-real-key"}


def make_profile(client, *, user_id=None, role="family", **update):
    uid = user_id or str(uuid.uuid4())
    h = auth_header(user_id=uid, role=role)
    client.get("/profiles/me", headers=h)
    if update:
        client.put("/profiles/me", headers=h, json=update)
    return uid


# --- доступ по ключу -------------------------------------------------


def test_stats_without_key_403(client):
    r = client.get("/internal/stats")
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_stats_with_wrong_key_403(client):
    assert client.get("/internal/stats", headers=WRONG_HEADERS).status_code == 403


def test_list_profiles_without_key_403(client):
    assert client.get("/internal/profiles").status_code == 403


def test_list_profiles_with_wrong_key_403(client):
    assert client.get("/internal/profiles", headers=WRONG_HEADERS).status_code == 403


def test_get_profile_without_key_403(client):
    assert client.get("/internal/profiles/whatever").status_code == 403


def test_verify_without_key_403(client):
    r = client.patch("/internal/profiles/whatever/verify", params={"is_verified": True})
    assert r.status_code == 403


def test_verify_with_wrong_key_403(client):
    r = client.patch(
        "/internal/profiles/whatever/verify",
        headers=WRONG_HEADERS,
        params={"is_verified": True},
    )
    assert r.status_code == 403


# --- /internal/stats ---------------------------------------------------


def test_stats_shape(client):
    make_profile(client, role="family", squad_id="squad-1")
    make_profile(client, role="local_historian", subscribed_to_search=True)
    searcher = make_profile(client, role="searcher")

    # верифицируем одного (searcher), чтобы pending_verification и by_role различались
    client.patch(
        f"/internal/profiles/{searcher}/verify",
        headers=INTERNAL_HEADERS,
        params={"is_verified": True},
    )

    r = client.get("/internal/stats", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "user_service"
    assert body["profiles_total"] == 3
    assert body["verified"] == 1
    assert body["pending_verification"] == 2
    assert body["subscribed_to_search"] == 1
    assert body["with_squad"] == 1
    assert body["by_role"] == {"family": 1, "local_historian": 1, "searcher": 1}
    # family не участвует в "ожидают верификации роли"
    assert body["pending_verification_by_role"] == {"local_historian": 1}
    assert body["avg_alert_radius_km"] == 20.0


# --- /internal/profiles --------------------------------------------------


def test_list_profiles_ok(client):
    make_profile(client, role="family", display_name="Иван", city="Орёл")
    make_profile(client, role="searcher", display_name="Пётр", city="Москва")

    r = client.get("/internal/profiles", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["limit"] == 50
    assert body["offset"] == 0
    names = {p["display_name"] for p in body["items"]}
    assert names == {"Иван", "Пётр"}


def test_list_profiles_filters_by_role(client):
    make_profile(client, role="family")
    make_profile(client, role="searcher")

    r = client.get("/internal/profiles", headers=INTERNAL_HEADERS, params={"role": "searcher"})
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["role"] == "searcher"


def test_list_profiles_filters_by_query(client):
    make_profile(client, display_name="Иван Орлов", city="Курск")
    make_profile(client, display_name="Пётр", city="Орёл")

    by_name = client.get(
        "/internal/profiles", headers=INTERNAL_HEADERS, params={"query": "Иван"}
    ).json()
    assert by_name["total"] == 1
    assert by_name["items"][0]["display_name"] == "Иван Орлов"

    by_city = client.get(
        "/internal/profiles", headers=INTERNAL_HEADERS, params={"query": "Орёл"}
    ).json()
    assert by_city["total"] == 1
    assert by_city["items"][0]["city"] == "Орёл"


def test_list_profiles_filters_by_is_verified(client):
    verified = make_profile(client)
    make_profile(client)
    client.patch(
        f"/internal/profiles/{verified}/verify",
        headers=INTERNAL_HEADERS,
        params={"is_verified": True},
    )

    r = client.get("/internal/profiles", headers=INTERNAL_HEADERS, params={"is_verified": True})
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == verified


def test_get_profile_ok(client):
    uid = make_profile(client)
    r = client.get(f"/internal/profiles/{uid}", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    assert r.json()["id"] == uid


def test_get_profile_missing_404(client):
    r = client.get(f"/internal/profiles/{uuid.uuid4()}", headers=INTERNAL_HEADERS)
    assert r.status_code == 404


# --- verify: обход обычной ролевой проверки -----------------------------


def test_verify_bypasses_role_restriction(client):
    target = make_profile(client, role="family")

    # обычный JWT family не может верифицировать (см. test_profiles.py)
    assert (
        client.patch(
            f"/profiles/{target}/verify",
            headers=auth_header(role="family"),
            json={"is_verified": True},
        ).status_code
        == 403
    )

    # а внутренний ключ — может, независимо от роли актора
    r = client.patch(
        f"/internal/profiles/{target}/verify",
        headers=INTERNAL_HEADERS,
        params={"is_verified": True},
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is True

    # изменение видно и через /internal/profiles/{id}, и через публичный /profiles/{id}
    assert (
        client.get(f"/internal/profiles/{target}", headers=INTERNAL_HEADERS).json()["is_verified"]
        is True
    )
    assert client.get(f"/profiles/{target}", headers=auth_header()).json()["is_verified"] is True


def test_verify_works_with_custom_actor_header(client):
    target = make_profile(client)
    r = client.patch(
        f"/internal/profiles/{target}/verify",
        headers={**INTERNAL_HEADERS, "X-Actor-Id": "admin-42"},
        params={"is_verified": True},
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is True


def test_verify_can_unset(client):
    target = make_profile(client)
    client.patch(
        f"/internal/profiles/{target}/verify",
        headers=INTERNAL_HEADERS,
        params={"is_verified": True},
    )
    r = client.patch(
        f"/internal/profiles/{target}/verify",
        headers=INTERNAL_HEADERS,
        params={"is_verified": False},
    )
    assert r.status_code == 200
    assert r.json()["is_verified"] is False


def test_verify_missing_profile_404(client):
    r = client.patch(
        f"/internal/profiles/{uuid.uuid4()}/verify",
        headers=INTERNAL_HEADERS,
        params={"is_verified": True},
    )
    assert r.status_code == 404


# --- семья для search_hq («Я потерялся») ---


def _link_family(client, inviter: str, invitee: str) -> None:
    code = client.post("/family-links/invite", headers=auth_header(user_id=inviter)).json()["code"]
    r = client.post("/family-links/redeem", headers=auth_header(user_id=invitee), json={"code": code})
    assert r.status_code == 204


def test_family_without_key_403(client):
    assert client.get("/internal/family/someone").status_code == 403
    assert client.get("/internal/family/someone", headers=WRONG_HEADERS).status_code == 403


def test_family_is_visible_from_both_sides(client):
    mom, kid, dad = (str(uuid.uuid4()) for _ in range(3))
    _link_family(client, mom, kid)
    _link_family(client, mom, dad)

    r = client.get(f"/internal/family/{mom}", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    assert r.json() == {"user_id": mom, "member_ids": [kid, dad]}

    kid_family = client.get(f"/internal/family/{kid}", headers=INTERNAL_HEADERS).json()
    assert kid_family["member_ids"] == [mom]


def test_family_of_lonely_user_is_empty(client):
    lonely = str(uuid.uuid4())
    r = client.get(f"/internal/family/{lonely}", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    assert r.json() == {"user_id": lonely, "member_ids": []}
