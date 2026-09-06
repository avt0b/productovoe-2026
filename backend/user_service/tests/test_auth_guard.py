import time
import uuid

import jwt

SECRET = "test-secret-test-secret-test-secret-0123456789"


def make_token(**overrides) -> str:
    now = int(time.time())
    payload = {
        "sub": str(uuid.uuid4()),
        "role": "searcher",
        "is_root": False,
        "iss": "auth_service",
        "iat": now,
        "exp": now + 900,
        "typ": "access",
    }
    payload.update(overrides)
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_whoami_requires_token(client):
    assert client.get("/whoami").status_code in (401, 403)  # нет заголовка Authorization


def test_whoami_accepts_valid_token(client):
    token = make_token(role="searcher")
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "searcher"
    assert r.json()["is_root"] is False


def test_whoami_rejects_wrong_secret(client):
    token = jwt.encode(
        {"sub": "x", "iss": "auth_service", "exp": int(time.time()) + 900, "typ": "access"},
        "not-the-secret",
        algorithm="HS256",
    )
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_whoami_rejects_non_access_token(client):
    token = make_token(typ="refresh")
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_whoami_rejects_expired_token(client):
    token = make_token(exp=int(time.time()) - 10)
    r = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
