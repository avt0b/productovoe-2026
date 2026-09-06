import jwt

from core.config import settings


def decode_access_token(token: str) -> dict:
    """Проверяет access-JWT, выпущенный auth_service (локально, без сети)."""
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
