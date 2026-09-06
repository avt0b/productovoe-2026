"""Служебная плоскость для admin_service: статистика и управление учётками.

Отличается от `/admin/*` только способом аутентификации: там нужен JWT
пользователя с `is_root`, здесь — общий внутренний ключ. Бизнес-логика
переиспользуется как есть (`UserAdminService`).
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from api.deps import DbSession, UserAdminServiceDep
from api.schemas.user import RoleUpdate, UserOut
from core.internal import require_internal_key
from core.models import Role, User

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


def _since(days: int) -> datetime:
    # Наивный UTC — одинаково работает и в Postgres, и в sqlite тестов.
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


@router.get("/stats", summary="Сводка по пользователям")
def stats(db: DbSession) -> dict:
    total = db.scalar(select(func.count(User.id))) or 0
    active = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    roots = db.scalar(select(func.count(User.id)).where(User.is_root.is_(True))) or 0

    by_role = {role.value: 0 for role in Role}
    for role, count in db.execute(select(User.role, func.count(User.id)).group_by(User.role)):
        key = role.value if isinstance(role, Role) else str(role)
        by_role[key] = count

    return {
        "service": "auth_service",
        "users_total": total,
        "users_active": active,
        "users_inactive": total - active,
        "roots": roots,
        "by_role": by_role,
        "registered_7d": db.scalar(
            select(func.count(User.id)).where(User.created_at >= _since(7))
        )
        or 0,
        "registered_30d": db.scalar(
            select(func.count(User.id)).where(User.created_at >= _since(30))
        )
        or 0,
    }


@router.get("/users", summary="Список пользователей с фильтрами")
def list_users(
    db: DbSession,
    query: Annotated[str | None, Query(description="поиск по email")] = None,
    role: Annotated[Role | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if query:
        conditions.append(User.email.ilike(f"%{query.strip().lower()}%"))
    if role is not None:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active.is_(is_active))

    total = db.scalar(select(func.count(User.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(User)
        .where(*conditions)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [UserOut.model_validate(u) for u in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, service: UserAdminServiceDep) -> UserOut:
    return UserOut.model_validate(service.get_user(user_id))


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_role(user_id: str, payload: RoleUpdate, service: UserAdminServiceDep) -> UserOut:
    return UserOut.model_validate(service.set_role(user_id, payload.role))


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_active(
    user_id: str,
    service: UserAdminServiceDep,
    is_active: Annotated[bool, Query()],
) -> UserOut:
    return UserOut.model_validate(service.set_active(user_id, is_active))


@router.patch("/users/{user_id}/root", response_model=UserOut)
def set_root(
    user_id: str,
    service: UserAdminServiceDep,
    is_root: Annotated[bool, Query()],
) -> UserOut:
    return UserOut.model_validate(service.set_root(user_id, is_root))


@router.get("/stats/timeseries", summary="Динамика регистраций")
def timeseries(
    db: DbSession,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    day = func.date(User.created_at).label("day")
    rows = db.execute(
        select(day, func.count(User.id))
        .where(User.created_at >= _since(days))
        .group_by(day)
        .order_by(day)
    ).all()
    return {
        "service": "auth_service",
        "days": days,
        "points": [{"date": str(value), "value": count} for value, count in rows],
    }
