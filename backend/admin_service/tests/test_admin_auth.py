from conftest import SUPERADMIN, auth_headers, login

from core.config import settings
from core.db import SessionLocal
from core.models import AdminUser


def test_login_returns_tokens_when_totp_disabled(client, superadmin):
    response = login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["mfa_required"] is False
    assert body["access_token"] and body["refresh_token"]


def test_login_rejects_wrong_password(client, superadmin):
    response = login(client, password="totally-wrong")
    assert response.status_code == 401


def test_login_rejects_unknown_email_without_leaking(client, superadmin):
    unknown = login(client, email="nobody@marshruty.ru", password="whatever-长")
    wrong = login(client, password="totally-wrong")
    # Одинаковый ответ: по коду и тексту нельзя понять, есть ли такая учётка.
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"]


def test_me_reports_policy_and_mfa_state(client, superadmin):
    response = client.get("/admin/auth/me", headers=auth_headers(client))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == SUPERADMIN["email"]
    assert body["totp_enabled"] is False
    assert body["mfa_satisfied"] is False
    assert body["totp_required_by_policy"] is settings.require_totp


def test_protected_endpoint_requires_token(client, superadmin):
    assert client.get("/admin/audit").status_code == 401


def test_refresh_rotates_and_detects_reuse(client, superadmin):
    first = login(client).json()
    old_refresh = first["refresh_token"]

    rotated = client.post("/admin/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    new_refresh = rotated.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Повторное использование старого токена — компрометация цепочки.
    replayed = client.post("/admin/auth/refresh", json={"refresh_token": old_refresh})
    assert replayed.status_code == 401

    # …и новый токен тоже перестаёт работать: погашены все сессии.
    after = client.post("/admin/auth/refresh", json={"refresh_token": new_refresh})
    assert after.status_code == 401


def test_logout_revokes_refresh_token(client, superadmin):
    body = login(client).json()
    assert client.post(
        "/admin/auth/logout", json={"refresh_token": body["refresh_token"]}
    ).status_code == 204
    assert client.post(
        "/admin/auth/refresh", json={"refresh_token": body["refresh_token"]}
    ).status_code == 401


def test_account_locks_after_repeated_failures(client, superadmin):
    for _ in range(settings.max_failed_attempts):
        assert login(client, password="nope-nope-nope").status_code == 401

    locked = login(client)  # даже с верным паролем
    assert locked.status_code == 423
    assert "заблокирован" in locked.json()["detail"].lower()


def test_change_password_revokes_all_sessions(client, superadmin):
    body = login(client).json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    changed = client.post(
        "/admin/auth/change-password",
        headers=headers,
        json={
            "current_password": SUPERADMIN["password"],
            "new_password": "another-strong-password",
        },
    )
    assert changed.status_code == 204

    assert client.post(
        "/admin/auth/refresh", json={"refresh_token": body["refresh_token"]}
    ).status_code == 401
    assert login(client, password="another-strong-password").status_code == 200


def test_inactive_admin_cannot_log_in(client, superadmin):
    with SessionLocal() as db:
        admin = db.get(AdminUser, superadmin.id)
        admin.is_active = False
        db.commit()

    assert login(client).status_code == 403
