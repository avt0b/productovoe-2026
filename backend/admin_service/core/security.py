"""Пароли, JWT админки, TOTP и коды восстановления.

JWT здесь подписывается ОТДЕЛЬНЫМ секретом (`ADMIN_JWT_SECRET`) и имеет свой
issuer, поэтому токен админки не пройдёт проверку в публичных сервисах, а
пользовательский токен — здесь.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from core.config import settings

_ph = PasswordHasher()

# Хэш-заглушка: сверяемся с ней, когда админа с таким email нет, чтобы время
# ответа не выдавало существование учётки.
_DUMMY_HASH = _ph.hash("dummy-password-for-constant-time-compare")

TOKEN_TYPE_ACCESS = "admin_access"
TOKEN_TYPE_MFA = "admin_mfa"

# Алфавит кодов восстановления без похожих символов (0/O, 1/I).
_RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


# --- пароли ----------------------------------------------------------------


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _ph.verify(password_hash, password)
        return True
    except (VerifyMismatchError, VerificationError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _ph.check_needs_rehash(password_hash)


def burn_time() -> None:
    """Прогнать argon2 вхолостую — против тайминг-атаки на существование email."""
    verify_password("nope", _DUMMY_HASH)


# --- JWT -------------------------------------------------------------------


def create_access_token(*, admin_id: str, email: str, role: str, mfa: bool) -> tuple[str, int]:
    """Возвращает (token, expires_in_seconds).

    `amr` (authentication methods references) фиксирует, какими факторами
    подтверждён вход: ["pwd"] или ["pwd", "otp"].
    """
    now = datetime.now(UTC)
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": admin_id,
        "email": email,
        "role": role,
        "amr": ["pwd", "otp"] if mfa else ["pwd"],
        "iss": settings.admin_jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "jti": str(uuid.uuid4()),
        "typ": TOKEN_TYPE_ACCESS,
    }
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
    return token, int(ttl.total_seconds())


def create_mfa_token(admin_id: str) -> tuple[str, int]:
    """Короткоживущий токен между «пароль принят» и «код введён».

    Сам по себе не даёт доступа ни к чему: обменивается только на /login/mfa.
    """
    now = datetime.now(UTC)
    ttl = timedelta(minutes=settings.mfa_token_ttl_minutes)
    payload = {
        "sub": admin_id,
        "iss": settings.admin_jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "jti": str(uuid.uuid4()),
        "typ": TOKEN_TYPE_MFA,
    }
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=settings.admin_jwt_algorithm)
    return token, int(ttl.total_seconds())


def decode_token(token: str, *, expected_type: str) -> dict:
    payload = jwt.decode(
        token,
        settings.admin_jwt_secret,
        algorithms=[settings.admin_jwt_algorithm],
        issuer=settings.admin_jwt_issuer,
        options={"require": ["exp", "sub", "iss"]},
    )
    if payload.get("typ") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    return payload


# --- refresh-токены --------------------------------------------------------


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)


# --- TOTP ------------------------------------------------------------------


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str) -> str:
    """otpauth://-ссылка для Google Authenticator / Aegis / 1Password.

    QR-код рисует фронтенд: гонять картинку через API незачем, а секрет
    в любом случае показывается один раз рядом с ним.
    """
    return pyotp.TOTP(secret).provisioning_uri(
        name=email, issuer_name=settings.totp_issuer_name
    )


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    normalized = code.strip().replace(" ", "").replace("-", "")
    if not normalized.isdigit():
        return False
    return pyotp.TOTP(secret).verify(normalized, valid_window=settings.totp_valid_window)


# --- коды восстановления ---------------------------------------------------


def generate_recovery_codes(count: int) -> list[str]:
    """Коды вида ABCD-EF23. Показываются пользователю ровно один раз."""
    codes = []
    for _ in range(count):
        raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(8))
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def normalize_recovery_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def hash_recovery_code(code: str) -> str:
    return hashlib.sha256(normalize_recovery_code(code).encode()).hexdigest()
