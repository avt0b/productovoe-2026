from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, TripServiceDep
from api.schemas.trip import RegistrationOut, TripOut, TripUpdate

router = APIRouter(prefix="/trips", tags=["trips (Выходные с поисковиком)"])


@router.get("", response_model=list[TripOut])
def list_trips(
    service: TripServiceDep,
    upcoming_only: Annotated[bool, Query()] = True,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TripOut]:
    rows = service.search(upcoming_only=upcoming_only, limit=limit, offset=offset)
    return [TripOut.model_validate(t) for t in rows]


@router.get("/{trip_id}", response_model=TripOut)
def get_trip(trip_id: str, service: TripServiceDep) -> TripOut:
    return TripOut.model_validate(service.get(trip_id))


@router.patch("/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: str, payload: TripUpdate, principal: CurrentPrincipal, service: TripServiceDep
) -> TripOut:
    return TripOut.model_validate(service.update(principal, trip_id, payload.to_update_dict()))


@router.post(
    "/{trip_id}/registrations", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED
)
def register_for_trip(
    trip_id: str, principal: CurrentPrincipal, service: TripServiceDep
) -> RegistrationOut:
    return RegistrationOut.model_validate(service.register(principal, trip_id))


@router.delete("/{trip_id}/registrations/me", status_code=status.HTTP_204_NO_CONTENT)
def cancel_registration(
    trip_id: str, principal: CurrentPrincipal, service: TripServiceDep
) -> None:
    service.cancel(principal, trip_id)


@router.get("/{trip_id}/registrations", response_model=list[RegistrationOut])
def list_registrations(
    trip_id: str, principal: CurrentPrincipal, service: TripServiceDep
) -> list[RegistrationOut]:
    rows = service.registrations_for(principal, trip_id)
    return [RegistrationOut.model_validate(r) for r in rows]
