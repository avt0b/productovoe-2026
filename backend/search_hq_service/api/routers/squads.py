from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, NeedServiceDep, SquadServiceDep, TripServiceDep
from api.schemas.need import NeedCreate, NeedOut
from api.schemas.squad import SquadCreate, SquadOut, SquadUpdate
from api.schemas.trip import TripCreate, TripOut
from core.models import NeedKind, NeedStatus, SquadKind

router = APIRouter(prefix="/squads", tags=["squads (поисковый штаб)"])


@router.post("", response_model=SquadOut, status_code=status.HTTP_201_CREATED)
def create_squad(
    payload: SquadCreate, principal: CurrentPrincipal, service: SquadServiceDep
) -> SquadOut:
    return SquadOut.model_validate(service.create(principal, payload.model_dump()))


@router.get("", response_model=list[SquadOut])
def list_squads(
    service: SquadServiceDep,
    region: Annotated[str | None, Query(max_length=120)] = None,
    kind: Annotated[SquadKind | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    min_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    min_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
    max_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    max_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SquadOut]:
    bbox = None
    if None not in (min_lat, min_lon, max_lat, max_lon):
        bbox = (min_lat, min_lon, max_lat, max_lon)
    rows = service.search(region=region, kind=kind, q=q, bbox=bbox, limit=limit, offset=offset)
    return [SquadOut.model_validate(s) for s in rows]


@router.get("/{squad_id}", response_model=SquadOut)
def get_squad(squad_id: str, service: SquadServiceDep) -> SquadOut:
    return SquadOut.model_validate(service.get(squad_id))


@router.patch("/{squad_id}", response_model=SquadOut)
def update_squad(
    squad_id: str, payload: SquadUpdate, principal: CurrentPrincipal, service: SquadServiceDep
) -> SquadOut:
    return SquadOut.model_validate(service.update(principal, squad_id, payload.to_update_dict()))


@router.delete("/{squad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_squad(squad_id: str, principal: CurrentPrincipal, service: SquadServiceDep) -> None:
    service.delete(principal, squad_id)


# --- вложенные потребности отряда ---


@router.get("/{squad_id}/needs", response_model=list[NeedOut])
def list_squad_needs(
    squad_id: str,
    service: NeedServiceDep,
    kind: Annotated[NeedKind | None, Query()] = None,
    status_: Annotated[NeedStatus | None, Query(alias="status")] = None,
) -> list[NeedOut]:
    rows = service.search(squad_id=squad_id, kind=kind, status=status_)
    return [NeedOut.model_validate(n) for n in rows]


@router.post("/{squad_id}/needs", response_model=NeedOut, status_code=status.HTTP_201_CREATED)
def create_squad_need(
    squad_id: str, payload: NeedCreate, principal: CurrentPrincipal, service: NeedServiceDep
) -> NeedOut:
    return NeedOut.model_validate(service.create(principal, squad_id, payload.model_dump()))


# --- вложенные выезды отряда ---


@router.get("/{squad_id}/trips", response_model=list[TripOut])
def list_squad_trips(squad_id: str, service: TripServiceDep) -> list[TripOut]:
    return [TripOut.model_validate(t) for t in service.search(squad_id=squad_id)]


@router.post("/{squad_id}/trips", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_squad_trip(
    squad_id: str, payload: TripCreate, principal: CurrentPrincipal, service: TripServiceDep
) -> TripOut:
    return TripOut.model_validate(service.create(principal, squad_id, payload.model_dump()))
