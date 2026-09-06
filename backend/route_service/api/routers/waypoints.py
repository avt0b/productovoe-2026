from fastapi import APIRouter, status

from api.deps import CurrentPrincipal, RouteServiceDep
from api.schemas.route import ReorderRequest, WaypointOut, WaypointUpdate

router = APIRouter(tags=["waypoints (точки маршрута)"])


@router.patch("/waypoints/{waypoint_id}", response_model=WaypointOut)
def update_waypoint(
    waypoint_id: str,
    payload: WaypointUpdate,
    principal: CurrentPrincipal,
    service: RouteServiceDep,
) -> WaypointOut:
    return WaypointOut.model_validate(
        service.update_waypoint(principal, waypoint_id, payload.to_update_dict())
    )


@router.delete("/waypoints/{waypoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_waypoint(
    waypoint_id: str, principal: CurrentPrincipal, service: RouteServiceDep
) -> None:
    service.delete_waypoint(principal, waypoint_id)


@router.post("/routes/{route_id}/waypoints/reorder", response_model=list[WaypointOut])
def reorder_waypoints(
    route_id: str,
    payload: ReorderRequest,
    principal: CurrentPrincipal,
    service: RouteServiceDep,
) -> list[WaypointOut]:
    rows = service.reorder_waypoints(principal, route_id, payload.ordered_ids)
    return [WaypointOut.model_validate(w) for w in rows]
