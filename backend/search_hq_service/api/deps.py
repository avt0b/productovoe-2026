from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import Principal, decode_access_token, principal_from_payload
from services.need_service import NeedService
from services.squad_service import SquadService
from services.trip_service import TripService

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


def get_squad_service(db: DbSession) -> SquadService:
    return SquadService(db)


def get_need_service(db: DbSession) -> NeedService:
    return NeedService(db)


def get_trip_service(db: DbSession) -> TripService:
    return TripService(db)


SquadServiceDep = Annotated[SquadService, Depends(get_squad_service)]
NeedServiceDep = Annotated[NeedService, Depends(get_need_service)]
TripServiceDep = Annotated[TripService, Depends(get_trip_service)]
