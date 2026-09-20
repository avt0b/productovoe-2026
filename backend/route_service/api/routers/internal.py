"""Служебная плоскость для admin_service: квест-маршруты и прогресс семей."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from api.deps import DbSession, RouteServiceDep
from api.schemas.route import PublishRequest, RouteOut
from core.internal import InternalActor, require_internal_key
from core.models import Route, RouteMode, RouteProgress, Waypoint

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


def _since(days: int) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


@router.get("/stats", summary="Сводка по маршрутам")
def stats(db: DbSession) -> dict:
    total = db.scalar(select(func.count(Route.id))) or 0
    published = db.scalar(select(func.count(Route.id)).where(Route.is_published.is_(True))) or 0

    by_mode = {mode.value: 0 for mode in RouteMode}
    for mode, count in db.execute(select(Route.mode, func.count(Route.id)).group_by(Route.mode)):
        by_mode[mode.value if isinstance(mode, RouteMode) else str(mode)] = count

    started = db.scalar(select(func.count(RouteProgress.id))) or 0
    completed = (
        db.scalar(
            select(func.count(RouteProgress.id)).where(RouteProgress.completed_at.is_not(None))
        )
        or 0
    )

    return {
        "service": "route_service",
        "routes_total": total,
        "published": published,
        "drafts": total - published,
        "by_mode": by_mode,
        "waypoints_total": db.scalar(select(func.count(Waypoint.id))) or 0,
        "avg_distance_km": round(db.scalar(select(func.avg(Route.distance_km))) or 0, 2),
        "progress_started": started,
        "progress_completed": completed,
        "completion_rate": round(completed / started, 3) if started else 0.0,
        "started_7d": db.scalar(
            select(func.count(RouteProgress.id)).where(RouteProgress.started_at >= _since(7))
        )
        or 0,
    }


@router.get("/routes", summary="Маршруты с фильтрами (включая черновики)")
def list_routes(
    db: DbSession,
    is_published: Annotated[bool | None, Query()] = None,
    mode: Annotated[RouteMode | None, Query()] = None,
    query: Annotated[str | None, Query(description="поиск по названию или городу")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if is_published is not None:
        conditions.append(Route.is_published.is_(is_published))
    if mode is not None:
        conditions.append(Route.mode == mode)
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(Route.title.ilike(pattern) | Route.city.ilike(pattern))

    total = db.scalar(select(func.count(Route.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Route)
        .where(*conditions)
        .order_by(Route.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [RouteOut.model_validate(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/routes/{route_id}/publish", response_model=RouteOut)
def set_published(
    route_id: str,
    payload: PublishRequest,
    actor: InternalActor,
    service: RouteServiceDep,
) -> RouteOut:
    return RouteOut.model_validate(service.set_published(actor, route_id, payload.is_published))


@router.delete("/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: str, actor: InternalActor, service: RouteServiceDep) -> None:
    service.delete(actor, route_id)
