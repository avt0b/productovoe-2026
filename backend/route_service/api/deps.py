from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import Principal, decode_access_token, principal_from_payload
from services.progress_service import ProgressService
from services.route_service import RouteService

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


def get_route_service(db: DbSession) -> RouteService:
    return RouteService(db)


def get_progress_service(db: DbSession) -> ProgressService:
    return ProgressService(db)


RouteServiceDep = Annotated[RouteService, Depends(get_route_service)]
ProgressServiceDep = Annotated[ProgressService, Depends(get_progress_service)]
