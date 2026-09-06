from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import Principal, decode_access_token, principal_from_payload
from services.profile_service import ProfileService

_bearer = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_db)]


def get_principal(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> Principal:
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal_from_payload(payload)


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]


def require_root(principal: CurrentPrincipal) -> Principal:
    if not principal.is_root:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора"
        )
    return principal


def get_profile_service(db: DbSession) -> ProfileService:
    return ProfileService(db)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
