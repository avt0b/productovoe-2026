def register(client, email="user@example.com", password="hackathon-2026", role="family"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "role": role}
    )


def login(client, email="user@example.com", password="hackathon-2026"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_register_returns_user_without_root(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "family"
    assert body["is_root"] is False
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_conflicts(client):
    register(client)
    r = register(client)
    assert r.status_code == 409


def test_register_rejects_short_password(client):
    r = register(client, password="short")
    assert r.status_code == 422


def test_login_and_access_me(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["token_type"] == "bearer"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_login_wrong_password_401(client):
    register(client)
    r = login(client, password="nope-nope-nope")
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_refresh_rotates_and_old_token_is_dead(client):
    register(client)
    tokens = login(client).json()

    r1 = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r1.status_code == 200
    new_tokens = r1.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # повторное использование старого refresh → отказ
    reuse = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401

    # и вся цепочка отозвана — свежий тоже больше не работает
    after_breach = client.post(
        "/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]}
    )
    assert after_breach.status_code == 401


def test_logout_revokes_refresh(client):
    register(client)
    tokens = login(client).json()
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_admin_endpoints_require_root(client):
    register(client)
    tokens = login(client).json()
    r = client.get("/admin/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 403


def test_change_password_revokes_sessions(client):
    register(client)
    tokens = login(client).json()
    r = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"current_password": "hackathon-2026", "new_password": "brand-new-pass-1"},
    )
    assert r.status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert login(client, password="hackathon-2026").status_code == 401
    assert login(client, password="brand-new-pass-1").status_code == 200
