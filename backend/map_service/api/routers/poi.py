from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, POIServiceDep
from api.schemas.poi import POICreate, POINearbyOut, POIOut, POIUpdate
from core.models import POIKind

router = APIRouter(prefix="/poi", tags=["poi (слой ВОВ)"])


@router.get("", response_model=list[POIOut])
def list_poi(
    service: POIServiceDep,
    kind: Annotated[POIKind | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    min_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    min_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
    max_lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    max_lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[POIOut]:
    bbox = None
    if None not in (min_lat, min_lon, max_lat, max_lon):
        bbox = (min_lat, min_lon, max_lat, max_lon)
    rows = service.search(kind=kind, q=q, bbox=bbox, limit=limit, offset=offset)
    return [POIOut.model_validate(r) for r in rows]


@router.get("/nearby", response_model=list[POINearbyOut])
def poi_nearby(
    service: POIServiceDep,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[float, Query(gt=0, le=500)] = 5,
    kind: Annotated[POIKind | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[POINearbyOut]:
    pairs = service.nearby(lat=lat, lon=lon, radius_km=radius_km, kind=kind, limit=limit)
    return [
        POINearbyOut(**POIOut.model_validate(poi).model_dump(), distance_km=round(dist, 3))
        for poi, dist in pairs
    ]


@router.post("", response_model=POIOut, status_code=status.HTTP_201_CREATED)
def create_poi(payload: POICreate, principal: CurrentPrincipal, service: POIServiceDep) -> POIOut:
    return POIOut.model_validate(service.create(principal, payload.model_dump()))


@router.get("/{poi_id}", response_model=POIOut)
def get_poi(poi_id: str, service: POIServiceDep) -> POIOut:
    return POIOut.model_validate(service.get(poi_id))


@router.patch("/{poi_id}", response_model=POIOut)
def update_poi(
    poi_id: str, payload: POIUpdate, principal: CurrentPrincipal, service: POIServiceDep
) -> POIOut:
    return POIOut.model_validate(service.update(principal, poi_id, payload.to_update_dict()))


@router.delete("/{poi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poi(poi_id: str, principal: CurrentPrincipal, service: POIServiceDep) -> None:
    service.delete(principal, poi_id)
