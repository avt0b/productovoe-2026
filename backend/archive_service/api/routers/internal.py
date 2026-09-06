"""Служебная плоскость для admin_service: «народный архив» и очередь модерации."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from api.deps import DbSession, EntryServiceDep
from api.schemas.entry import EntryOut, ReviewRequest
from core.internal import InternalActor, require_internal_key
from core.models import ArchiveEntry, EntryKind, EntryStatus

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


def _since(days: int) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


@router.get("/stats", summary="Сводка по народному архиву")
def stats(db: DbSession) -> dict:
    by_status = {s.value: 0 for s in EntryStatus}
    for entry_status, count in db.execute(
        select(ArchiveEntry.status, func.count(ArchiveEntry.id)).group_by(ArchiveEntry.status)
    ):
        key = entry_status.value if isinstance(entry_status, EntryStatus) else str(entry_status)
        by_status[key] = count

    by_kind = {k.value: 0 for k in EntryKind}
    for kind, count in db.execute(
        select(ArchiveEntry.kind, func.count(ArchiveEntry.id)).group_by(ArchiveEntry.kind)
    ):
        by_kind[kind.value if isinstance(kind, EntryKind) else str(kind)] = count

    return {
        "service": "archive_service",
        "entries_total": db.scalar(select(func.count(ArchiveEntry.id))) or 0,
        "by_status": by_status,
        "by_kind": by_kind,
        # Главная метрика дашборда: сколько заявок ждёт краеведа.
        "moderation_queue": by_status.get(EntryStatus.pending.value, 0),
        "verified_7d": db.scalar(
            select(func.count(ArchiveEntry.id)).where(
                ArchiveEntry.status == EntryStatus.verified,
                ArchiveEntry.reviewed_at >= _since(7),
            )
        )
        or 0,
        "submitted_7d": db.scalar(
            select(func.count(ArchiveEntry.id)).where(ArchiveEntry.created_at >= _since(7))
        )
        or 0,
        "geo_tagged": db.scalar(
            select(func.count(ArchiveEntry.id)).where(ArchiveEntry.lat.is_not(None))
        )
        or 0,
    }


@router.get("/entries", summary="Записи архива с фильтрами")
def list_entries(
    db: DbSession,
    entry_status: Annotated[EntryStatus | None, Query(alias="status")] = None,
    kind: Annotated[EntryKind | None, Query()] = None,
    query: Annotated[str | None, Query(description="поиск по заголовку")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if entry_status is not None:
        conditions.append(ArchiveEntry.status == entry_status)
    if kind is not None:
        conditions.append(ArchiveEntry.kind == kind)
    if query:
        conditions.append(ArchiveEntry.title.ilike(f"%{query.strip()}%"))

    total = db.scalar(select(func.count(ArchiveEntry.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(ArchiveEntry)
        .where(*conditions)
        .order_by(ArchiveEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [EntryOut.model_validate(e) for e in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/entries/{entry_id}/verify", response_model=EntryOut)
def verify_entry(
    entry_id: str,
    payload: ReviewRequest,
    actor: InternalActor,
    service: EntryServiceDep,
) -> EntryOut:
    return EntryOut.model_validate(service.verify(actor, entry_id, note=payload.note))


@router.post("/entries/{entry_id}/reject", response_model=EntryOut)
def reject_entry(
    entry_id: str,
    payload: ReviewRequest,
    actor: InternalActor,
    service: EntryServiceDep,
) -> EntryOut:
    return EntryOut.model_validate(service.reject(actor, entry_id, note=payload.note))


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: str, actor: InternalActor, service: EntryServiceDep) -> None:
    service.delete(actor, entry_id)


@router.get("/stats/timeseries", summary="Динамика проверки записей архива")
def timeseries(
    db: DbSession,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    day = func.date(ArchiveEntry.reviewed_at).label("day")
    rows = db.execute(
        select(day, func.count(ArchiveEntry.id))
        .where(
            ArchiveEntry.status == EntryStatus.verified,
            ArchiveEntry.reviewed_at >= _since(days),
        )
        .group_by(day)
        .order_by(day)
    ).all()
    return {
        "service": "archive_service",
        "days": days,
        "points": [{"date": str(value), "value": count} for value, count in rows],
    }
