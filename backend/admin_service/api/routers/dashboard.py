"""Дашборд: плитки KPI, график за 30 дней и состояние сервисов."""

from typing import Annotated

from fastapi import APIRouter, Query

from api.deps import AuditServiceDep, AuthedAdmin, DashboardServiceDep
from api.schemas.audit import AuditEntryOut

router = APIRouter(prefix="/admin/dashboard", tags=["admin: дашборд"])


@router.get("/overview", summary="Плитки KPI и сводка по всем сервисам")
async def overview(
    admin: AuthedAdmin,
    service: DashboardServiceDep,
    audit: AuditServiceDep,
    recent_actions: Annotated[int, Query(ge=0, le=50)] = 10,
) -> dict:
    data = await service.overview()
    # Нижний блок макета — «Журнал последних действий модерации».
    data["recent_audit"] = [
        AuditEntryOut.model_validate(row) for row in audit.recent(recent_actions)
    ]
    return data


@router.get("/timeseries", summary="Ряды для графика динамики")
async def timeseries(
    admin: AuthedAdmin,
    service: DashboardServiceDep,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    return await service.timeseries(days)


@router.get("/health", summary="Доступность сервисов платформы")
async def health(admin: AuthedAdmin, service: DashboardServiceDep) -> dict:
    return await service.health()
