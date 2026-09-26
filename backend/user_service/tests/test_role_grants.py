"""POST /role-grants/redeem — роль по ключу с NFC-метки."""

import uuid

import pytest
from conftest import auth_header

import services.role_grant_service as role_grant_service_module
from core.config import settings
from core.exceptions import ServiceUnavailable
from core.models import Profile, RoleGrant
from core.role_keys import hash_key, parse_keys

SEARCHER_KEY = "searcher-key-" + "s" * 30
HISTORIAN_KEY = "historian-key-" + "h" * 30


@pytest.fixture(autouse=True)
def grant_keys(monkeypatch):
    monkeypatch.setattr(
        settings,
        "role_grant_keys",
        f"searcher:{hash_key(SEARCHER_KEY)}, local_historian:{hash_key(HISTORIAN_KEY)}",
    )


@pytest.fixture()
def accounts(monkeypatch):
    """Учётки «в auth_service»: id → {role, is_root}. Роль меняет set_role."""
    users: dict[str, dict] = {}
    calls: list[tuple[str, str]] = []

    def set_role(*, user_id: str, role: str) -> None:
        calls.append((user_id, role))
        users[user_id]["role"] = role

    monkeypatch.setattr(role_grant_service_module.auth_client, "get_user", users.get)
    monkeypatch.setattr(role_grant_service_module.auth_client, "set_role", set_role)
    return users, calls


def new_user(users: dict, *, role: str = "family", is_root: bool = False) -> str:
    user_id = str(uuid.uuid4())
    users[user_id] = {"id": user_id, "role": role, "is_root": is_root}
    return user_id


def redeem(client, key: str, user_id: str, nickname: str = "Иван"):
    return client.post(
        "/role-grants/redeem", json={"key": key, "user_id": user_id, "nickname": nickname}
    )


def test_searcher_key_grants_searcher(client, accounts, db_session):
    users, calls = accounts
    user_id = new_user(users)

    r = redeem(client, SEARCHER_KEY, user_id)
    assert r.status_code == 200
    assert r.json() == {
        "user_id": user_id,
        "role": "searcher",
        "previous_role": "family",
        "already": False,
    }
    assert calls == [(user_id, "searcher")]

    profile = db_session.get(Profile, user_id)
    assert profile.role == "searcher"
    assert profile.is_verified is True

    grant = db_session.query(RoleGrant).one()
    assert (grant.user_id, grant.nickname, grant.previous_role) == (user_id, "Иван", "family")
    assert grant.key_fingerprint == hash_key(SEARCHER_KEY)[:12]


def test_historian_key_grants_historian(client, accounts):
    users, _ = accounts
    user_id = new_user(users, role="searcher")

    body = redeem(client, HISTORIAN_KEY, user_id).json()
    assert body["role"] == "local_historian"
    assert body["previous_role"] == "searcher"
    assert users[user_id]["role"] == "local_historian"


def test_no_token_needed(client, accounts):
    """Токен не нужен и не мешает: выдаём тому, чей uuid прислали."""
    users, _ = accounts
    user_id = new_user(users)
    r = client.post(
        "/role-grants/redeem",
        headers=auth_header(user_id=str(uuid.uuid4())),
        json={"key": SEARCHER_KEY, "user_id": user_id},
    )
    assert r.status_code == 200
    assert users[user_id]["role"] == "searcher"


def test_unknown_key_rejected(client, accounts):
    users, calls = accounts
    user_id = new_user(users)
    r = redeem(client, "not-a-real-key-" + "x" * 30, user_id)
    assert r.status_code == 404
    assert r.json()["detail"] == "Метка не подходит"
    assert calls == []


def test_no_keys_configured(client, accounts, monkeypatch):
    monkeypatch.setattr(settings, "role_grant_keys", "")
    users, _ = accounts
    assert redeem(client, SEARCHER_KEY, new_user(users)).status_code == 404


def test_unknown_user_rejected(client, accounts):
    r = redeem(client, SEARCHER_KEY, str(uuid.uuid4()))
    assert r.status_code == 404
    assert r.json()["detail"] == "Пользователь не найден"


def test_not_a_uuid_rejected(client, accounts):
    assert redeem(client, SEARCHER_KEY, "ivan").status_code == 422


def test_root_untouched(client, accounts):
    users, calls = accounts
    user_id = new_user(users, is_root=True)
    assert redeem(client, SEARCHER_KEY, user_id).status_code == 409
    assert calls == []


def test_repeat_is_already(client, accounts, db_session):
    users, calls = accounts
    user_id = new_user(users)
    redeem(client, SEARCHER_KEY, user_id)

    body = redeem(client, SEARCHER_KEY, user_id).json()
    assert body["already"] is True
    assert body["previous_role"] == "searcher"
    # В auth_service второй раз не ходили, но в журнале оба прикладывания.
    assert calls == [(user_id, "searcher")]
    assert db_session.query(RoleGrant).count() == 2


def test_pending_application_for_same_role_closed(client, accounts):
    users, _ = accounts
    user_id = new_user(users)
    client.post(
        "/role-applications",
        headers=auth_header(user_id=user_id),
        json={"requested_role": "local_historian", "full_name": "Иван", "contact": "@ivan"},
    )

    redeem(client, HISTORIAN_KEY, user_id)

    mine = client.get("/role-applications/mine", headers=auth_header(user_id=user_id)).json()
    assert mine[0]["status"] == "approved"
    assert mine[0]["previous_role"] == "family"


def test_auth_service_down_is_503(client, accounts, monkeypatch):
    def down(user_id: str):
        raise ServiceUnavailable("auth_service недоступен")

    monkeypatch.setattr(role_grant_service_module.auth_client, "get_user", down)
    assert redeem(client, SEARCHER_KEY, str(uuid.uuid4())).status_code == 503


def test_parse_keys_skips_broken_entries():
    good = hash_key("k")
    keys = parse_keys(f"searcher:{good}, admin:{good}, local_historian:short, ,")
    assert keys == {good: "searcher"}
