"""Тесты служебной плоскости /internal/* (используется admin_service)."""

from core.config import settings

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}
WRONG_HEADERS = {"X-Internal-Key": "not-the-real-key"}


def register(client, email="user@example.com", password="hackathon-2026", role="family"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "role": role}
    )


def login(client, email="user@example.com", password="hackathon-2026"):
    return client.post("/auth/login", json={"email": email, "password": password})


# --- доступ по ключу -------------------------------------------------


def test_stats_without_key_403(client):
    r = client.get("/internal/stats")
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_stats_with_wrong_key_403(client):
    r = client.get("/internal/stats", headers=WRONG_HEADERS)
    assert r.status_code == 403


def test_users_list_without_key_403(client):
    assert client.get("/internal/users").status_code == 403


def test_users_list_with_wrong_key_403(client):
    assert client.get("/internal/users", headers=WRONG_HEADERS).status_code == 403


def test_get_user_without_key_403(client):
    assert client.get("/internal/users/whatever").status_code == 403


def test_set_role_without_key_403(client):
    r = client.patch("/internal/users/whatever/role", json={"role": "mentor"})
    assert r.status_code == 403


def test_set_active_without_key_403(client):
    r = client.patch("/internal/users/whatever/active", params={"is_active": False})
    assert r.status_code == 403


def test_set_root_without_key_403(client):
    r = client.patch("/internal/users/whatever/root", params={"is_root": True})
    assert r.status_code == 403


def test_timeseries_without_key_403(client):
    assert client.get("/internal/stats/timeseries").status_code == 403


# --- /internal/stats ---------------------------------------------------


def test_stats_shape(client):
    # Не полагаемся на нулевую базу: локальный .env сервиса может задавать
    # BOOTSTRAP_ROOT_EMAIL/PASSWORD, из-за чего при старте уже есть root-юзер.
    baseline = client.get("/internal/stats", headers=INTERNAL_HEADERS).json()

    register(client, email="a@example.com", role="family")
    register(client, email="b@example.com", role="local_historian")

    r = client.get("/internal/stats", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "auth_service"
    assert body["users_total"] == baseline["users_total"] + 2
    assert body["users_active"] == baseline["users_active"] + 2
    assert body["users_inactive"] == baseline["users_inactive"]
    assert isinstance(body["by_role"], dict)
    assert body["by_role"]["family"] == baseline["by_role"]["family"] + 1
    assert body["by_role"]["local_historian"] == baseline["by_role"]["local_historian"] + 1
    assert body["registered_7d"] == baseline["registered_7d"] + 2
    assert body["registered_30d"] == baseline["registered_30d"] + 2


def test_timeseries_shape(client):
    before = client.get(
        "/internal/stats/timeseries", headers=INTERNAL_HEADERS, params={"days": 7}
    ).json()
    before_total = sum(p["value"] for p in before["points"])

    register(client)
    r = client.get("/internal/stats/timeseries", headers=INTERNAL_HEADERS, params={"days": 7})
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "auth_service"
    assert body["days"] == 7
    assert isinstance(body["points"], list)
    after_total = sum(p["value"] for p in body["points"])
    assert after_total == before_total + 1
    assert all("date" in p and isinstance(p["value"], int) for p in body["points"])


# --- /internal/users ----------------------------------------------------


def test_list_users_ok(client):
    baseline_total = client.get("/internal/users", headers=INTERNAL_HEADERS).json()["total"]

    register(client, email="a@example.com", role="family")
    register(client, email="b@example.com", role="local_historian")

    r = client.get("/internal/users", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == baseline_total + 2
    assert body["limit"] == 50
    assert body["offset"] == 0
    emails = {u["email"] for u in body["items"]}
    assert {"a@example.com", "b@example.com"} <= emails


def test_list_users_filters_by_role_and_query(client):
    register(client, email="a@example.com", role="family")
    register(client, email="b@example.com", role="local_historian")

    by_role = client.get(
        "/internal/users", headers=INTERNAL_HEADERS, params={"role": "local_historian"}
    ).json()
    assert by_role["total"] == 1
    assert by_role["items"][0]["email"] == "b@example.com"

    by_query = client.get(
        "/internal/users", headers=INTERNAL_HEADERS, params={"query": "a@example"}
    ).json()
    assert by_query["total"] == 1
    assert by_query["items"][0]["email"] == "a@example.com"


def test_list_users_filters_by_is_active(client):
    register(client, email="a@example.com")
    uid = register(client, email="b@example.com").json()["id"]
    client.patch(
        f"/internal/users/{uid}/active", headers=INTERNAL_HEADERS, params={"is_active": False}
    )

    inactive = client.get(
        "/internal/users", headers=INTERNAL_HEADERS, params={"is_active": False}
    ).json()
    assert inactive["total"] == 1
    assert inactive["items"][0]["email"] == "b@example.com"


def test_get_user_ok(client):
    uid = register(client).json()["id"]
    r = client.get(f"/internal/users/{uid}", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    assert r.json()["id"] == uid


def test_get_user_missing_404(client):
    r = client.get("/internal/users/does-not-exist", headers=INTERNAL_HEADERS)
    assert r.status_code == 404


# --- мутации -------------------------------------------------------------


def test_set_role_changes_role_and_bypasses_self_assign_restriction(client):
    uid = register(client).json()["id"]

    # Через /auth/register роль "moderator" нельзя выбрать самому — а через
    # внутренний ключ admin_service обязан иметь возможность её назначить.
    r = client.patch(
        f"/internal/users/{uid}/role", headers=INTERNAL_HEADERS, json={"role": "moderator"}
    )
    assert r.status_code == 200
    assert r.json()["role"] == "moderator"

    check = client.get(f"/internal/users/{uid}", headers=INTERNAL_HEADERS)
    assert check.json()["role"] == "moderator"


def test_set_role_missing_user_404(client):
    r = client.patch(
        "/internal/users/does-not-exist/role", headers=INTERNAL_HEADERS, json={"role": "mentor"}
    )
    assert r.status_code == 404


def test_set_active_false_revokes_sessions_and_blocks_login(client):
    register(client)
    tokens = login(client).json()
    uid = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).json()["id"]

    r = client.patch(
        f"/internal/users/{uid}/active", headers=INTERNAL_HEADERS, params={"is_active": False}
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    # видно через /internal/users/{id}
    assert client.get(f"/internal/users/{uid}", headers=INTERNAL_HEADERS).json()["is_active"] is False

    # логин теперь запрещён, а старый refresh отозван
    assert login(client).status_code == 403
    assert client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).status_code == 401


def test_set_root_updates_flag(client):
    uid = register(client).json()["id"]
    assert (
        client.get(f"/internal/users/{uid}", headers=INTERNAL_HEADERS).json()["is_root"]
        is False
    )

    r = client.patch(
        f"/internal/users/{uid}/root", headers=INTERNAL_HEADERS, params={"is_root": True}
    )
    assert r.status_code == 200
    assert r.json()["is_root"] is True
    assert (
        client.get(f"/internal/users/{uid}", headers=INTERNAL_HEADERS).json()["is_root"]
        is True
    )
