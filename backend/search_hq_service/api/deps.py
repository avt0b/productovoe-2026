from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import Principal, decode_access_token, principal_from_payload
from services.bump_service import BumpService
from services.excursion_service import ExcursionService
from services.need_service import NeedService
from services.squad_service import SquadService
from services.trip_service import TripService

_bearer = HTTPBearer(auto_error=True)
_optional_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def _principal_from_credentials(creds: HTTPAuthorizationCredentials) -> Principal:
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal_from_payload(payload)


def get_principal(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> Principal:
    return _principal_from_credentials(creds)


def get_optional_principal(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)],
) -> Principal | None:
    """Публичная ручка, которая с токеном отвечает подробнее. Битый токен — 401, а не аноним."""
    return _principal_from_credentials(creds) if creds is not None else None


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]
OptionalPrincipal = Annotated[Principal | None, Depends(get_optional_principal)]


def get_squad_service(db: DbSession) -> SquadService:
    return SquadService(db)


def get_need_service(db: DbSession) -> NeedService:
    return NeedService(db)


def get_trip_service(db: DbSession) -> TripService:
    return TripService(db)


def get_excursion_service(db: DbSession) -> ExcursionService:
    return ExcursionService(db)


def get_bump_service(db: DbSession) -> BumpService:
    return BumpService(db)


SquadServiceDep = Annotated[SquadService, Depends(get_squad_service)]
NeedServiceDep = Annotated[NeedService, Depends(get_need_service)]
TripServiceDep = Annotated[TripService, Depends(get_trip_service)]
ExcursionServiceDep = Annotated[ExcursionService, Depends(get_excursion_service)]
BumpServiceDep = Annotated[BumpService, Depends(get_bump_service)]
