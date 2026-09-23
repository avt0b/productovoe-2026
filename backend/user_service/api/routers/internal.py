"""Служебная плоскость для admin_service: профили и подписки."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from api.deps import AchievementServiceDep, DbSession, NotificationServiceDep, ProfileServiceDep
from api.schemas.achievement import AwardOut, AwardRequest
from api.schemas.notification import (
    BroadcastNearbyOut,
    BroadcastNearbyRequest,
    NotifyUsersOut,
    NotifyUsersRequest,
)
from api.schemas.profile import ProfileOut
from core.internal import InternalActor, require_internal_key
from core.models import Profile

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


@router.get("/stats", summary="Сводка по профилям")
def stats(db: DbSession) -> dict:
    total = db.scalar(select(func.count(Profile.id))) or 0
    verified = db.scalar(select(func.count(Profile.id)).where(Profile.is_verified.is_(True))) or 0
    subscribed = (
        db.scalar(select(func.count(Profile.id)).where(Profile.subscribed_to_search.is_(True))) or 0
    )
    with_squad = db.scalar(select(func.count(Profile.id)).where(Profile.squad_id.is_not(None))) or 0

    by_role: dict[str, int] = {}
    for role, count in db.execute(
        select(Profile.role, func.count(Profile.id)).group_by(Profile.role)
    ):
        by_role[str(role)] = count

    # Плитка «На верификации ролей» в админке показывает разбивку:
    # сколько краеведов, поисковиков и наставников ждут подтверждения статуса.
    pending_by_role: dict[str, int] = {}
    for role, count in db.execute(
        select(Profile.role, func.count(Profile.id))
        .where(Profile.is_verified.is_(False), Profile.role != "family")
        .group_by(Profile.role)
    ):
        pending_by_role[str(role)] = count

    return {
        "service": "user_service",
        "profiles_total": total,
        "verified": verified,
        "pending_verification": total - verified,
        "subscribed_to_search": subscribed,
        "with_squad": with_squad,
        "by_role": by_role,
        "pending_verification_by_role": pending_by_role,
        "avg_alert_radius_km": round(db.scalar(select(func.avg(Profile.alert_radius_km))) or 0, 1),
    }


@router.get("/profiles", summary="Список профилей с фильтрами")
def list_profiles(
    db: DbSession,
    query: Annotated[str | None, Query(description="поиск по имени или городу")] = None,
    role: Annotated[str | None, Query()] = None,
    is_verified: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(Profile.display_name.ilike(pattern) | Profile.city.ilike(pattern))
    if role:
        conditions.append(Profile.role == role)
    if is_verified is not None:
        conditions.append(Profile.is_verified.is_(is_verified))

    total = db.scalar(select(func.count(Profile.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Profile)
        .where(*conditions)
        .order_by(Profile.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [ProfileOut.model_validate(p) for p in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/profiles/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: str, service: ProfileServiceDep) -> ProfileOut:
    return ProfileOut.model_validate(service.get(profile_id))


@router.patch("/profiles/{profile_id}/verify", response_model=ProfileOut)
def set_verified(
    profile_id: str,
    actor: InternalActor,
    service: ProfileServiceDep,
    is_verified: Annotated[bool, Query()],
) -> ProfileOut:
    return ProfileOut.model_validate(service.set_verified(actor, profile_id, is_verified))


@router.post("/notifications/broadcast-nearby", response_model=BroadcastNearbyOut)
def broadcast_nearby(
    payload: BroadcastNearbyRequest, service: NotificationServiceDep
) -> BroadcastNearbyOut:
    """Вызывается map_service при появлении новой точки «Последнего боя»: создаёт
    уведомления всем подписчикам, у кого точка попала в их собственный радиус."""
    count = service.broadcast_nearby(
        lat=payload.lat,
        lon=payload.lon,
        kind=payload.kind,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
    )
    return BroadcastNearbyOut(notified=count)


@router.post("/notifications/send", response_model=NotifyUsersOut)
def notify_users(payload: NotifyUsersRequest, service: NotificationServiceDep) -> NotifyUsersOut:
    """Адресная рассылка из другого сервиса — конкретным людям по user_id.

    search_hq_service зовёт её, когда краевед открыл сбор: записанные узнают об
    этом сразу, а не когда сами заглянут в экскурсию."""
    count = service.notify_users(
        user_ids=payload.user_ids,
        kind=payload.kind,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
    )
    return NotifyUsersOut(notified=count)


@router.post("/achievements/award", response_model=AwardOut)
def award_achievement(payload: AwardRequest, service: AchievementServiceDep) -> AwardOut:
    """Вызывается сервисами-источниками события (route_service на завершении
    маршрута, archive_service на верификации, search_hq_service на выезде/
    донате). Идемпотентно — повторный вызов с тем же (user_id, code) не
    создаёт дубликат и не шлёт уведомление повторно."""
    _, awarded = service.award(user_id=payload.user_id, code=payload.code)
    return AwardOut(code=payload.code, awarded=awarded)
