from dataclasses import dataclass

import jwt

from core.config import settings


@dataclass(frozen=True)
class Principal:
    """Пользователь, извлечённый из access-JWT, выпущенного auth_service."""

    user_id: str
    role: str
    is_root: bool


def decode_access_token(token: str) -> dict:
    """Проверяет подпись и claims локально (HS256, общий секрет), без сети."""
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "sub", "iss"]},
    )
    if payload.get("typ") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return payload


def principal_from_payload(payload: dict) -> Principal:
    return Principal(
        user_id=payload["sub"],
        role=payload.get("role", "family"),
        is_root=bool(payload.get("is_root", False)),
    )
