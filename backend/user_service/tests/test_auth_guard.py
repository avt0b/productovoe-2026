import time

import jwt
from conftest import SECRET, auth_header


def test_whoami_requires_token(client):
    assert client.get("/whoami").status_code in (401, 403)


def test_whoami_accepts_valid_token(client):
    r = client.get("/whoami", headers=auth_header(role="searcher"))
    assert r.status_code == 200
    assert r.json()["role"] == "searcher"


def test_whoami_rejects_wrong_secret(client):
    token = jwt.encode(
        {"sub": "x", "iss": "auth_service", "exp": int(time.time()) + 900, "typ": "access"},
        "not-the-secret",
        algorithm="HS256",
    )
    assert client.get("/whoami", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_whoami_rejects_non_access_token(client):
    token = jwt.encode(
        {"sub": "x", "iss": "auth_service", "exp": int(time.time()) + 900, "typ": "refresh"},
        SECRET,
        algorithm="HS256",
    )
    assert client.get("/whoami", headers={"Authorization": f"Bearer {token}"}).status_code == 401
