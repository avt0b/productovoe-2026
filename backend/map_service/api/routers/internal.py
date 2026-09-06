"""Служебная плоскость для admin_service: слой «ВОВ» и карта «Последний бой»."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from api.deps import DbSession, LastStandServiceDep, POIServiceDep
from api.schemas.last_stand import LastStandOut, LastStandStatusUpdate
from api.schemas.poi import POIOut
from core.internal import InternalActor, require_internal_key
from core.models import LastStandPoint, LastStandStatus, POIKind, PointOfInterest

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


def _since(days: int) -> datetime:
    # Наивный UTC — одинаково сравнивается и в Postgres, и в sqlite тестов.
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


@router.get("/stats", summary="Сводка по точкам на карте")
def stats(db: DbSession) -> dict:
    poi_by_kind = {kind.value: 0 for kind in POIKind}
    for kind, count in db.execute(
        select(PointOfInterest.kind, func.count(PointOfInterest.id)).group_by(PointOfInterest.kind)
    ):
        poi_by_kind[kind.value if isinstance(kind, POIKind) else str(kind)] = count

    ls_by_status = {s.value: 0 for s in LastStandStatus}
    for point_status, count in db.execute(
        select(LastStandPoint.status, func.count(LastStandPoint.id)).group_by(LastStandPoint.status)
    ):
        key = point_status.value if isinstance(point_status, LastStandStatus) else str(point_status)
        ls_by_status[key] = count

    return {
        "service": "map_service",
        "poi_total": db.scalar(select(func.count(PointOfInterest.id))) or 0,
        "poi_by_kind": poi_by_kind,
        "poi_added_30d": db.scalar(
            select(func.count(PointOfInterest.id)).where(PointOfInterest.created_at >= _since(30))
        )
        or 0,
        "last_stand_total": db.scalar(select(func.count(LastStandPoint.id))) or 0,
        "last_stand_by_status": ls_by_status,
        # Красные метки прототипа: обнаружено, но ещё не подтверждено архивом.
        "last_stand_unconfirmed": ls_by_status.get(LastStandStatus.discovered.value, 0),
        "last_stand_added_7d": db.scalar(
            select(func.count(LastStandPoint.id)).where(LastStandPoint.created_at >= _since(7))
        )
        or 0,
    }


@router.get("/last-stand", summary="Точки «Последнего боя» с фильтрами")
def list_last_stand(
    db: DbSession,
    point_status: Annotated[LastStandStatus | None, Query(alias="status")] = None,
    query: Annotated[str | None, Query(description="поиск по ФИО или части")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if point_status is not None:
        conditions.append(LastStandPoint.status == point_status)
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(
            LastStandPoint.soldier_name.ilike(pattern) | LastStandPoint.unit.ilike(pattern)
        )

    total = db.scalar(select(func.count(LastStandPoint.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(LastStandPoint)
        .where(*conditions)
        .order_by(LastStandPoint.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [LastStandOut.model_validate(p) for p in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/last-stand/{point_id}/status", response_model=LastStandOut)
def set_last_stand_status(
    point_id: str,
    payload: LastStandStatusUpdate,
    actor: InternalActor,
    service: LastStandServiceDep,
) -> LastStandOut:
    return LastStandOut.model_validate(service.set_status(actor, point_id, payload.status))


@router.delete("/last-stand/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_last_stand(point_id: str, actor: InternalActor, service: LastStandServiceDep) -> None:
    service.delete(actor, point_id)


@router.get("/poi", summary="Точки слоя «ВОВ» с фильтрами")
def list_poi(
    db: DbSession,
    kind: Annotated[POIKind | None, Query()] = None,
    query: Annotated[str | None, Query(description="поиск по названию")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if kind is not None:
        conditions.append(PointOfInterest.kind == kind)
    if query:
        conditions.append(PointOfInterest.title.ilike(f"%{query.strip()}%"))

    total = db.scalar(select(func.count(PointOfInterest.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(PointOfInterest)
        .where(*conditions)
        .order_by(PointOfInterest.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [POIOut.model_validate(p) for p in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/poi/{poi_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poi(poi_id: str, actor: InternalActor, service: POIServiceDep) -> None:
    service.delete(actor, poi_id)


@router.get("/stats/timeseries", summary="Динамика появления точек «Последнего боя»")
def timeseries(
    db: DbSession,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    """Ряд «по дням» для графика на дашборде админки."""
    day = func.date(LastStandPoint.created_at).label("day")
    rows = db.execute(
        select(day, func.count(LastStandPoint.id))
        .where(LastStandPoint.created_at >= _since(days))
        .group_by(day)
        .order_by(day)
    ).all()
    return {
        "service": "map_service",
        "days": days,
        "points": [{"date": str(value), "value": count} for value, count in rows],
    }
