import pyotp
from conftest import SUPERADMIN, auth_headers, login

from core.config import settings


def _enable_totp(client) -> tuple[str, list[str], dict[str, str]]:
    """Проходит setup → confirm и возвращает (секрет, коды восстановления, headers)."""
    headers = auth_headers(client)
    setup = client.post("/admin/auth/totp/setup", headers=headers).json()
    secret = setup["secret"]
    assert setup["otpauth_uri"].startswith("otpauth://totp/")

    confirmed = client.post(
        "/admin/auth/totp/confirm",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert confirmed.status_code == 200
    codes = confirmed.json()["codes"]
    assert len(codes) == settings.recovery_codes_count
    return secret, codes, headers


def test_setup_returns_otpauth_uri(client, superadmin):
    setup = client.post("/admin/auth/totp/setup", headers=auth_headers(client))
    assert setup.status_code == 200
    body = setup.json()
    assert body["secret"]
    assert "issuer=" in body["otpauth_uri"]


def test_confirm_rejects_wrong_code(client, superadmin):
    headers = auth_headers(client)
    client.post("/admin/auth/totp/setup", headers=headers)
    bad = client.post("/admin/auth/totp/confirm", headers=headers, json={"code": "000000"})
    assert bad.status_code == 401


def test_login_requires_second_factor_once_enabled(client, superadmin):
    secret, _codes, _headers = _enable_totp(client)

    first = login(client).json()
    assert first["mfa_required"] is True
    assert first["mfa_token"]
    assert first.get("access_token") is None  # токенов на первом шаге нет

    second = client.post(
        "/admin/auth/login/mfa",
        json={"mfa_token": first["mfa_token"], "code": pyotp.TOTP(secret).now()},
    )
    assert second.status_code == 200
    assert second.json()["access_token"]


def test_mfa_rejects_wrong_code(client, superadmin):
    _enable_totp(client)
    first = login(client).json()
    bad = client.post(
        "/admin/auth/login/mfa",
        json={"mfa_token": first["mfa_token"], "code": "123456"},
    )
    assert bad.status_code == 401


def test_recovery_code_works_once(client, superadmin):
    _secret, codes, _headers = _enable_totp(client)
    code = codes[0]

    first = login(client).json()
    used = client.post(
        "/admin/auth/login/mfa", json={"mfa_token": first["mfa_token"], "code": code}
    )
    assert used.status_code == 200

    again = login(client).json()
    replay = client.post(
        "/admin/auth/login/mfa", json={"mfa_token": again["mfa_token"], "code": code}
    )
    assert replay.status_code == 401


def test_me_reports_mfa_satisfied_after_second_factor(client, superadmin):
    secret, _codes, _ = _enable_totp(client)
    first = login(client).json()
    tokens = client.post(
        "/admin/auth/login/mfa",
        json={"mfa_token": first["mfa_token"], "code": pyotp.TOTP(secret).now()},
    ).json()

    me = client.get(
        "/admin/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).json()
    assert me["totp_enabled"] is True
    assert me["mfa_satisfied"] is True
    assert me["unused_recovery_codes"] == settings.recovery_codes_count


def test_disable_totp_requires_password_and_code(client, superadmin):
    secret, _codes, headers = _enable_totp(client)

    wrong = client.post(
        "/admin/auth/totp/disable",
        headers=headers,
        json={"password": "not-my-password", "code": pyotp.TOTP(secret).now()},
    )
    assert wrong.status_code == 400

    ok = client.post(
        "/admin/auth/totp/disable",
        headers=headers,
        json={"password": SUPERADMIN["password"], "code": pyotp.TOTP(secret).now()},
    )
    assert ok.status_code == 204
    assert login(client).json()["mfa_required"] is False
