"""Служебная плоскость для admin_service: очередь «Живого фото» и мемориал."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select

from api.deps import ClipServiceDep, DbSession
from api.schemas.clip import ClipOut, ClipUpdate
from core.internal import InternalActor, require_internal_key
from core.models import ClipShare, ClipStatus, MemorialClip

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


def _since(days: int) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


@router.get("/stats", summary="Сводка по «Живому фото»")
def stats(db: DbSession) -> dict:
    by_status = {s.value: 0 for s in ClipStatus}
    for clip_status, count in db.execute(
        select(MemorialClip.status, func.count(MemorialClip.id)).group_by(MemorialClip.status)
    ):
        key = clip_status.value if isinstance(clip_status, ClipStatus) else str(clip_status)
        by_status[key] = count

    return {
        "service": "media_service",
        "clips_total": db.scalar(select(func.count(MemorialClip.id))) or 0,
        "by_status": by_status,
        # То, за чем админ следит в первую очередь: длина очереди и аварии.
        "queue_depth": by_status.get(ClipStatus.queued.value, 0)
        + by_status.get(ClipStatus.processing.value, 0),
        "failed": by_status.get(ClipStatus.failed.value, 0),
        "public": db.scalar(
            select(func.count(MemorialClip.id)).where(MemorialClip.is_public.is_(True))
        )
        or 0,
        "shares_total": db.scalar(select(func.count(ClipShare.id))) or 0,
        "created_7d": db.scalar(
            select(func.count(MemorialClip.id)).where(MemorialClip.created_at >= _since(7))
        )
        or 0,
    }


@router.get("/clips", summary="Заявки на оживление с фильтрами")
def list_clips(
    db: DbSession,
    clip_status: Annotated[ClipStatus | None, Query(alias="status")] = None,
    is_public: Annotated[bool | None, Query()] = None,
    query: Annotated[str | None, Query(description="поиск по имени бойца")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if clip_status is not None:
        conditions.append(MemorialClip.status == clip_status)
    if is_public is not None:
        conditions.append(MemorialClip.is_public.is_(is_public))
    if query:
        conditions.append(MemorialClip.soldier_name.ilike(f"%{query.strip()}%"))

    total = db.scalar(select(func.count(MemorialClip.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(MemorialClip)
        .where(*conditions)
        .order_by(MemorialClip.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [ClipOut.model_validate(c) for c in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/clips/{clip_id}", response_model=ClipOut)
def update_clip(
    clip_id: str,
    payload: ClipUpdate,
    actor: InternalActor,
    service: ClipServiceDep,
) -> ClipOut:
    """Снять клип с публикации или поправить текст — модерация мемориала."""
    return ClipOut.model_validate(service.update(actor, clip_id, payload.to_update_dict()))


@router.post("/clips/{clip_id}/retry", response_model=ClipOut)
def retry_clip(clip_id: str, actor: InternalActor, service: ClipServiceDep) -> ClipOut:
    return ClipOut.model_validate(service.retry(actor, clip_id))


@router.delete("/clips/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clip(clip_id: str, actor: InternalActor, service: ClipServiceDep) -> None:
    service.delete(actor, clip_id)
