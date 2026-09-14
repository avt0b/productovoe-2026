from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import BumpServiceDep, CurrentPrincipal, ExcursionServiceDep, OptionalPrincipal
from api.schemas.excursion import (
    BumpIn,
    BumpOut,
    ExcursionCreate,
    ExcursionOut,
    ExcursionUpdate,
    GatheringOut,
    GatheringStartIn,
    MyExcursionsOut,
    ParticipantOut,
)

router = APIRouter(prefix="/excursions", tags=["excursions (экскурсии краеведов и бамп)"])


@router.get("", response_model=list[ExcursionOut])
def list_excursions(
    service: ExcursionServiceDep,
    principal: OptionalPrincipal,
    upcoming_only: Annotated[bool, Query()] = True,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ExcursionOut]:
    views = service.search(principal, upcoming_only=upcoming_only, limit=limit, offset=offset)
    return [ExcursionOut.from_view(view) for view in views]


@router.get("/mine", response_model=MyExcursionsOut)
def my_excursions(principal: CurrentPrincipal, service: ExcursionServiceDep) -> MyExcursionsOut:
    guiding, joined = service.mine(principal)
    return MyExcursionsOut(
        guiding=[ExcursionOut.from_view(view) for view in guiding],
        joined=[ExcursionOut.from_view(view) for view in joined],
    )


@router.post("", response_model=ExcursionOut, status_code=status.HTTP_201_CREATED)
def create_excursion(
    payload: ExcursionCreate, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> ExcursionOut:
    return ExcursionOut.from_view(service.create(principal, payload.model_dump()))


@router.get("/{excursion_id}", response_model=ExcursionOut)
def get_excursion(
    excursion_id: str, principal: OptionalPrincipal, service: ExcursionServiceDep
) -> ExcursionOut:
    return ExcursionOut.from_view(service.detail(principal, excursion_id))


@router.patch("/{excursion_id}", response_model=ExcursionOut)
def update_excursion(
    excursion_id: str,
    payload: ExcursionUpdate,
    principal: CurrentPrincipal,
    service: ExcursionServiceDep,
) -> ExcursionOut:
    view = service.update(principal, excursion_id, payload.to_update_dict())
    return ExcursionOut.from_view(view)


@router.post("/{excursion_id}/cancel", response_model=ExcursionOut)
def cancel_excursion(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> ExcursionOut:
    return ExcursionOut.from_view(service.cancel(principal, excursion_id))


# --- запись участников ---


@router.post(
    "/{excursion_id}/registrations",
    response_model=ParticipantOut,
    status_code=status.HTTP_201_CREATED,
)
def register_for_excursion(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> ParticipantOut:
    return ParticipantOut.model_validate(service.register(principal, excursion_id))


@router.delete("/{excursion_id}/registrations/me", status_code=status.HTTP_204_NO_CONTENT)
def cancel_registration(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> None:
    service.cancel_registration(principal, excursion_id)


@router.get("/{excursion_id}/participants", response_model=list[ParticipantOut])
def list_participants(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> list[ParticipantOut]:
    rows = service.participants(principal, excursion_id)
    return [ParticipantOut.model_validate(row) for row in rows]


# --- сбор группы и бамп ---


@router.post("/{excursion_id}/gathering/start", response_model=GatheringOut)
def start_gathering(
    excursion_id: str,
    payload: GatheringStartIn,
    principal: CurrentPrincipal,
    service: ExcursionServiceDep,
) -> GatheringOut:
    state = service.start_gathering(
        principal, excursion_id, lat=payload.lat, lon=payload.lon, accuracy_m=payload.accuracy_m
    )
    return GatheringOut.from_state(state)


@router.post("/{excursion_id}/gathering/finish", response_model=GatheringOut)
def finish_gathering(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> GatheringOut:
    return GatheringOut.from_state(service.finish_gathering(principal, excursion_id))


@router.get("/{excursion_id}/gathering", response_model=GatheringOut)
def gathering_state(
    excursion_id: str, principal: CurrentPrincipal, service: ExcursionServiceDep
) -> GatheringOut:
    return GatheringOut.from_state(service.gathering_state(principal, excursion_id))


@router.post("/{excursion_id}/bumps", response_model=BumpOut)
def bump(
    excursion_id: str, payload: BumpIn, principal: CurrentPrincipal, service: BumpServiceDep
) -> BumpOut:
    # Синхронный обработчик: FastAPI держит его в пуле потоков, и ожидание пары
    # до пары секунд не блокирует остальные запросы.
    result = service.bump(
        principal,
        excursion_id,
        lat=payload.lat,
        lon=payload.lon,
        accuracy_m=payload.accuracy_m,
        shaken_ms_ago=payload.shaken_ms_ago,
    )
    return BumpOut.from_result(result)
