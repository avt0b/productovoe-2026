from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.db import get_db
from core.security import Principal, decode_access_token, principal_from_payload
from services.clip_service import ClipService

_required_bearer = HTTPBearer(auto_error=True)
_optional_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _principal_or_401(creds: HTTPAuthorizationCredentials) -> Principal:
    try:
        return principal_from_payload(decode_access_token(creds.credentials))
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_principal(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_required_bearer)],
) -> Principal:
    return _principal_or_401(creds)


def get_optional_principal(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)],
) -> Principal | None:
    if creds is None:
        return None
    return _principal_or_401(creds)


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]
OptionalPrincipal = Annotated[Principal | None, Depends(get_optional_principal)]


def require_render_worker(
    principal: OptionalPrincipal,
    x_worker_token: Annotated[str | None, Header()] = None,
) -> None:
    """Переходы состояний рендера. Пускаем воркер по токену, либо модератора/root."""
    if settings.render_worker_token and x_worker_token == settings.render_worker_token:
        return
    if principal and (principal.is_root or principal.role == "moderator"):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Только воркер рендера или модератор"
    )


def get_clip_service(db: DbSession) -> ClipService:
    return ClipService(db)


ClipServiceDep = Annotated[ClipService, Depends(get_clip_service)]
