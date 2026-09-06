"""Служебная плоскость для admin_service: отряды, потребности, сборы, выезды."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from api.deps import DbSession, NeedServiceDep
from api.schemas.need import NeedOut
from api.schemas.squad import SquadOut
from api.schemas.trip import TripOut
from core.internal import InternalActor, require_internal_key
from core.models import (
    Donation,
    NeedKind,
    NeedStatus,
    RegistrationStatus,
    Squad,
    SquadNeed,
    TripRegistration,
    VolunteerTrip,
)

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(require_internal_key)],
)


def _since(days: int) -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days)


def _today():
    return datetime.now(UTC).date()


@router.get("/stats", summary="Сводка по поисковому штабу")
def stats(db: DbSession) -> dict:
    needs_by_kind = {kind.value: 0 for kind in NeedKind}
    for kind, count in db.execute(
        select(SquadNeed.kind, func.count(SquadNeed.id)).group_by(SquadNeed.kind)
    ):
        needs_by_kind[kind.value if isinstance(kind, NeedKind) else str(kind)] = count

    funds_filter = SquadNeed.kind == NeedKind.funds
    target = db.scalar(select(func.sum(SquadNeed.target_amount)).where(funds_filter)) or 0
    collected = db.scalar(select(func.sum(SquadNeed.collected_amount)).where(funds_filter)) or 0

    volunteers_filter = SquadNeed.kind == NeedKind.volunteers
    volunteers_needed = (
        db.scalar(
            select(func.sum(SquadNeed.target_amount)).where(
                volunteers_filter, SquadNeed.status == NeedStatus.open
            )
        )
        or 0
    )

    return {
        "service": "search_hq_service",
        "squads_total": db.scalar(select(func.count(Squad.id))) or 0,
        "needs_total": db.scalar(select(func.count(SquadNeed.id))) or 0,
        "needs_open": db.scalar(
            select(func.count(SquadNeed.id)).where(SquadNeed.status == NeedStatus.open)
        )
        or 0,
        "needs_by_kind": needs_by_kind,
        "funds_target": int(target),
        "funds_collected": int(collected),
        "funds_progress": round(collected / target, 3) if target else 0.0,
        "donations_count": db.scalar(select(func.count(Donation.id))) or 0,
        "donations_7d": db.scalar(
            select(func.count(Donation.id)).where(Donation.created_at >= _since(7))
        )
        or 0,
        "volunteers_needed_open": int(volunteers_needed),
        "trips_total": db.scalar(select(func.count(VolunteerTrip.id))) or 0,
        "trips_upcoming": db.scalar(
            select(func.count(VolunteerTrip.id)).where(VolunteerTrip.starts_on >= _today())
        )
        or 0,
        "registrations_active": db.scalar(
            select(func.count(TripRegistration.id)).where(
                TripRegistration.status == RegistrationStatus.registered
            )
        )
        or 0,
    }


@router.get("/squads", summary="Отряды")
def list_squads(
    db: DbSession,
    query: Annotated[str | None, Query(description="поиск по названию или региону")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if query:
        pattern = f"%{query.strip()}%"
        conditions.append(Squad.name.ilike(pattern) | Squad.region.ilike(pattern))

    total = db.scalar(select(func.count(Squad.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Squad)
        .where(*conditions)
        .order_by(Squad.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [SquadOut.model_validate(s) for s in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/needs", summary="Потребности и сборы")
def list_needs(
    db: DbSession,
    need_status: Annotated[NeedStatus | None, Query(alias="status")] = None,
    kind: Annotated[NeedKind | None, Query()] = None,
    squad_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if need_status is not None:
        conditions.append(SquadNeed.status == need_status)
    if kind is not None:
        conditions.append(SquadNeed.kind == kind)
    if squad_id:
        conditions.append(SquadNeed.squad_id == squad_id)

    total = db.scalar(select(func.count(SquadNeed.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(SquadNeed)
        .where(*conditions)
        .order_by(SquadNeed.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [NeedOut.model_validate(n) for n in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/needs/{need_id}/close", response_model=NeedOut)
def close_need(need_id: str, actor: InternalActor, service: NeedServiceDep) -> NeedOut:
    return NeedOut.model_validate(service.close(actor, need_id))


@router.get("/trips", summary="Выезды «Выходные с поисковиком»")
def list_trips(
    db: DbSession,
    upcoming_only: Annotated[bool, Query()] = False,
    squad_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    conditions = []
    if upcoming_only:
        conditions.append(VolunteerTrip.starts_on >= _today())
    if squad_id:
        conditions.append(VolunteerTrip.squad_id == squad_id)

    total = db.scalar(select(func.count(VolunteerTrip.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(VolunteerTrip)
        .where(*conditions)
        .order_by(VolunteerTrip.starts_on.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return {
        "items": [TripOut.model_validate(t) for t in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
