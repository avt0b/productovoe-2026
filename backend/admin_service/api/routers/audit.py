"""Журнал действий администраторов. Только чтение — записи неизменяемы."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Query

from api.deps import AuditServiceDep, AuthedAdmin
from api.schemas.audit import AuditEntryOut, AuditPage
from core.models import AuditOutcome

router = APIRouter(prefix="/admin/audit", tags=["admin: журнал аудита"])


@router.get("", response_model=AuditPage, summary="Журнал действий с фильтрами")
def list_audit(
    admin: AuthedAdmin,
    service: AuditServiceDep,
    actor_id: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    target_service: Annotated[str | None, Query()] = None,
    outcome: Annotated[AuditOutcome | None, Query()] = None,
    days: Annotated[int | None, Query(ge=1, le=365)] = None,
    query: Annotated[str | None, Query(description="поиск по объекту или автору")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditPage:
    since = datetime.now(UTC) - timedelta(days=days) if days else None
    rows, total = service.search(
        actor_id=actor_id,
        action=action,
        target_service=target_service,
        outcome=outcome,
        since=since,
        query=query,
        limit=limit,
        offset=offset,
    )
    return AuditPage(
        items=[AuditEntryOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", summary="Сводка по журналу за период")
def audit_stats(
    admin: AuthedAdmin,
    service: AuditServiceDep,
    days: Annotated[int, Query(ge=1, le=365)] = 7,
) -> dict:
    return service.stats_since(datetime.now(UTC) - timedelta(days=days))
