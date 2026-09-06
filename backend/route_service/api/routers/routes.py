from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import (
    CurrentPrincipal,
    OptionalPrincipal,
    ProgressServiceDep,
    RouteServiceDep,
)
from api.schemas.route import (
    CompleteWaypointRequest,
    ProgressOut,
    PublishRequest,
    RouteCreate,
    RouteDetailOut,
    RouteOut,
    RouteUpdate,
    WaypointCreate,
    WaypointOut,
)
from core.models import RouteMode

router = APIRouter(prefix="/routes", tags=["routes (семейный навигатор)"])


@router.get("", response_model=list[RouteOut])
def list_routes(
    service: RouteServiceDep,
    mode: Annotated[RouteMode | None, Query()] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RouteOut]:
    rows = service.search_public(mode=mode, city=city, limit=limit, offset=offset)
    return [RouteOut.model_validate(r) for r in rows]


@router.get("/mine", response_model=list[RouteOut])
def my_routes(principal: CurrentPrincipal, service: RouteServiceDep) -> list[RouteOut]:
    return [RouteOut.model_validate(r) for r in service.list_mine(principal)]


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(
    payload: RouteCreate, principal: CurrentPrincipal, service: RouteServiceDep
) -> RouteOut:
    return RouteOut.model_validate(service.create(principal, payload.model_dump()))


@router.get("/{route_id}", response_model=RouteDetailOut)
def get_route(
    route_id: str, principal: OptionalPrincipal, service: RouteServiceDep
) -> RouteDetailOut:
    return RouteDetailOut.model_validate(service.get_visible(principal, route_id))


@router.patch("/{route_id}", response_model=RouteOut)
def update_route(
    route_id: str, payload: RouteUpdate, principal: CurrentPrincipal, service: RouteServiceDep
) -> RouteOut:
    return RouteOut.model_validate(
        service.update(principal, route_id, payload.to_update_dict())
    )


@router.post("/{route_id}/publish", response_model=RouteOut)
def publish_route(
    route_id: str,
    payload: PublishRequest,
    principal: CurrentPrincipal,
    service: RouteServiceDep,
) -> RouteOut:
    return RouteOut.model_validate(
        service.set_published(principal, route_id, payload.is_published)
    )


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: str, principal: CurrentPrincipal, service: RouteServiceDep) -> None:
    service.delete(principal, route_id)


# --- точки маршрута ---

@router.get("/{route_id}/waypoints", response_model=list[WaypointOut])
def list_waypoints(
    route_id: str, principal: OptionalPrincipal, service: RouteServiceDep
) -> list[WaypointOut]:
    return [WaypointOut.model_validate(w) for w in service.waypoints_of(principal, route_id)]


@router.post(
    "/{route_id}/waypoints", response_model=WaypointOut, status_code=status.HTTP_201_CREATED
)
def add_waypoint(
    route_id: str,
    payload: WaypointCreate,
    principal: CurrentPrincipal,
    service: RouteServiceDep,
) -> WaypointOut:
    return WaypointOut.model_validate(
        service.add_waypoint(principal, route_id, payload.model_dump())
    )


# --- прогресс семьи ---

@router.post("/{route_id}/progress/start", response_model=ProgressOut)
def start_progress(
    route_id: str, principal: CurrentPrincipal, service: ProgressServiceDep
) -> ProgressOut:
    return ProgressOut.model_validate(service.start(principal, route_id))


@router.get("/{route_id}/progress/me", response_model=ProgressOut)
def my_progress(
    route_id: str, principal: CurrentPrincipal, service: ProgressServiceDep
) -> ProgressOut:
    return ProgressOut.model_validate(service.get_mine(principal, route_id))


@router.post("/{route_id}/progress/complete-waypoint", response_model=ProgressOut)
def complete_waypoint(
    route_id: str,
    payload: CompleteWaypointRequest,
    principal: CurrentPrincipal,
    service: ProgressServiceDep,
) -> ProgressOut:
    return ProgressOut.model_validate(
        service.complete_waypoint(principal, route_id, payload.waypoint_id)
    )
