from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, LastStandServiceDep
from api.schemas.last_stand import (
    LastStandCreate,
    LastStandNearbyOut,
    LastStandOut,
    LastStandStatusUpdate,
    LastStandUpdate,
)
from core.models import LastStandStatus

router = APIRouter(prefix="/last-stand", tags=["last-stand (Последний бой)"])


@router.get("", response_model=list[LastStandOut])
def list_points(
    service: LastStandServiceDep,
    status_: Annotated[LastStandStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    min_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    min_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
    max_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    max_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LastStandOut]:
    bbox = None
    if None not in (min_lat, min_lon, max_lat, max_lon):
        bbox = (min_lat, min_lon, max_lat, max_lon)
    rows = service.search(status=status_, q=q, bbox=bbox, limit=limit, offset=offset)
    return [LastStandOut.model_validate(r) for r in rows]


@router.get("/mine", response_model=list[LastStandOut])
def my_points(
    principal: CurrentPrincipal,
    service: LastStandServiceDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LastStandOut]:
    """Точки «Последнего боя», добавленные самим запрашивающим."""
    rows = service.search(created_by=principal.user_id, limit=limit, offset=offset)
    return [LastStandOut.model_validate(r) for r in rows]


@router.get("/nearby", response_model=list[LastStandNearbyOut])
def points_nearby(
    service: LastStandServiceDep,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=500)] = 20,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[LastStandNearbyOut]:
    pairs = service.nearby(lat=lat, lon=lon, radius_km=radius_km, limit=limit)
    return [
        LastStandNearbyOut(
            **LastStandOut.model_validate(p).model_dump(), distance_km=round(dist, 3)
        )
        for p, dist in pairs
    ]


@router.post("", response_model=LastStandOut, status_code=status.HTTP_201_CREATED)
def create_point(
    payload: LastStandCreate, principal: CurrentPrincipal, service: LastStandServiceDep
) -> LastStandOut:
    return LastStandOut.model_validate(service.create(principal, payload.model_dump()))


@router.get("/{point_id}", response_model=LastStandOut)
def get_point(point_id: str, service: LastStandServiceDep) -> LastStandOut:
    return LastStandOut.model_validate(service.get(point_id))


@router.patch("/{point_id}", response_model=LastStandOut)
def update_point(
    point_id: str,
    payload: LastStandUpdate,
    principal: CurrentPrincipal,
    service: LastStandServiceDep,
) -> LastStandOut:
    return LastStandOut.model_validate(
        service.update(principal, point_id, payload.to_update_dict())
    )


@router.patch("/{point_id}/status", response_model=LastStandOut)
def set_point_status(
    point_id: str,
    payload: LastStandStatusUpdate,
    principal: CurrentPrincipal,
    service: LastStandServiceDep,
) -> LastStandOut:
    return LastStandOut.model_validate(service.set_status(principal, point_id, payload.status))


@router.delete("/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_point(point_id: str, principal: CurrentPrincipal, service: LastStandServiceDep) -> None:
    service.delete(principal, point_id)
