from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import Principal, decode_access_token, principal_from_payload
from services.last_stand_service import LastStandService
from services.poi_service import POIService

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


def get_poi_service(db: DbSession) -> POIService:
    return POIService(db)


def get_last_stand_service(db: DbSession) -> LastStandService:
    return LastStandService(db)


POIServiceDep = Annotated[POIService, Depends(get_poi_service)]
LastStandServiceDep = Annotated[LastStandService, Depends(get_last_stand_service)]
