from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import ChatServiceDep, CurrentPrincipal, TripServiceDep
from api.schemas.chat import ChatMessageCreate, ChatMessageOut
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


# Раньше `/{trip_id}`: иначе «mine» разобрался бы как id выезда.
@router.get("/mine", response_model=list[TripOut])
def my_trips(
    principal: CurrentPrincipal,
    service: TripServiceDep,
    upcoming_only: Annotated[bool, Query()] = True,
) -> list[TripOut]:
    """Выезды, на которые записан сам запрашивающий."""
    return [TripOut.model_validate(t) for t in service.mine(principal, upcoming_only=upcoming_only)]


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
def cancel_registration(trip_id: str, principal: CurrentPrincipal, service: TripServiceDep) -> None:
    service.cancel(principal, trip_id)


@router.get("/{trip_id}/registrations", response_model=list[RegistrationOut])
def list_registrations(
    trip_id: str, principal: CurrentPrincipal, service: TripServiceDep
) -> list[RegistrationOut]:
    rows = service.registrations_for(principal, trip_id)
    return [RegistrationOut.model_validate(r) for r in rows]


# --- чат сбора ---


@router.get("/{trip_id}/messages", response_model=list[ChatMessageOut])
def list_trip_messages(
    trip_id: str,
    principal: CurrentPrincipal,
    service: ChatServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ChatMessageOut]:
    rows = service.trip_messages(principal, trip_id, limit=limit, offset=offset)
    return [ChatMessageOut.model_validate(r) for r in rows]


@router.post(
    "/{trip_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED
)
def post_trip_message(
    trip_id: str, payload: ChatMessageCreate, principal: CurrentPrincipal, service: ChatServiceDep
) -> ChatMessageOut:
    return ChatMessageOut.model_validate(service.post_trip_message(principal, trip_id, payload.body))
