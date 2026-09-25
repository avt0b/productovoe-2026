from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import (
    ArchivePromptServiceDep,
    CurrentPrincipal,
    MediaPromptServiceDep,
    OptionalPrincipal,
    ProgressServiceDep,
    RouteServiceDep,
)
from api.schemas.route import (
    ArchivePromptOut,
    CompleteWaypointRequest,
    MediaPromptOut,
    ProgressOut,
    PublishRequest,
    RouteAutoGenerateRequest,
    RouteCreate,
    RouteDetailOut,
    RouteOut,
    RouteUpdate,
    WaypointCreate,
    WaypointOut,
)
from core.models import RouteMode

router = APIRouter(prefix="/routes", tags=["routes (семейный навигатор)"])


@router.get("", response_model=list[RouteOut])
def list_routes(
    service: RouteServiceDep,
    mode: Annotated[RouteMode | None, Query()] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[RouteOut]:
    rows = service.search_public(mode=mode, city=city, limit=limit, offset=offset)
    return [RouteOut.model_validate(r) for r in rows]


@router.get("/mine", response_model=list[RouteOut])
def my_routes(principal: CurrentPrincipal, service: RouteServiceDep) -> list[RouteOut]:
    return [RouteOut.model_validate(r) for r in service.list_mine(principal)]


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(
    payload: RouteCreate, principal: CurrentPrincipal, service: RouteServiceDep
) -> RouteOut:
    return RouteOut.model_validate(service.create(principal, payload.model_dump()))


@router.post("/auto-generate", response_model=RouteDetailOut, status_code=status.HTTP_201_CREATED)
async def auto_generate_route(
    payload: RouteAutoGenerateRequest, principal: CurrentPrincipal, service: RouteServiceDep
) -> RouteDetailOut:
    """Автосборка черновика маршрута из точек слоя «ВОВ» рядом с координатой —
    «автоматически строить квест-маршруты» (модуль 2 ТЗ). Результат не
    публикуется сам: контент (задания/аудио/AR) автор добавляет вручную."""
    route = await service.auto_generate(principal, payload.model_dump())
    return RouteDetailOut.model_validate(route)


@router.get("/{route_id}", response_model=RouteDetailOut)
def get_route(
    route_id: str, principal: OptionalPrincipal, service: RouteServiceDep
) -> RouteDetailOut:
    return RouteDetailOut.model_validate(service.get_visible(principal, route_id))


@router.get("/{route_id}/archive-prompts", response_model=list[ArchivePromptOut])
async def archive_prompts(
    route_id: str, principal: OptionalPrincipal, service: ArchivePromptServiceDep
) -> list[ArchivePromptOut]:
    """Неподтверждённые заметки «народного архива» рядом с точками маршрута —
    подсказка «помоги проверить» из п.5 ТЗ. Вызывается отдельно от списка точек,
    чтобы не тормозить обычный просмотр маршрута походом в archive_service."""
    prompts = await service.prompts_for_route(principal, route_id)
    return [ArchivePromptOut(**vars(p)) for p in prompts]


@router.get("/{route_id}/media-prompts", response_model=list[MediaPromptOut])
async def media_prompts(
    route_id: str, principal: OptionalPrincipal, service: MediaPromptServiceDep
) -> list[MediaPromptOut]:
    """Точки маршрута без «живого фото» — подсказка «оживить фото бойца из
    этого захоронения» (п.7 ТЗ, интеграция «Живого фото» с маршрутами)."""
    prompts = await service.prompts_for_route(principal, route_id)
    return [MediaPromptOut(**vars(p)) for p in prompts]


@router.patch("/{route_id}", response_model=RouteOut)
def update_route(
    route_id: str, payload: RouteUpdate, principal: CurrentPrincipal, service: RouteServiceDep
) -> RouteOut:
    return RouteOut.model_validate(service.update(principal, route_id, payload.to_update_dict()))


@router.post("/{route_id}/publish", response_model=RouteOut)
def publish_route(
    route_id: str,
    payload: PublishRequest,
    principal: CurrentPrincipal,
    service: RouteServiceDep,
) -> RouteOut:
    return RouteOut.model_validate(service.set_published(principal, route_id, payload.is_published))


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: str, principal: CurrentPrincipal, service: RouteServiceDep) -> None:
    service.delete(principal, route_id)


# --- точки маршрута ---


@router.get("/{route_id}/waypoints", response_model=list[WaypointOut])
def list_waypoints(
    route_id: str, principal: OptionalPrincipal, service: RouteServiceDep
) -> list[WaypointOut]:
    return [WaypointOut.model_validate(w) for w in service.waypoints_of(principal, route_id)]


@router.post(
    "/{route_id}/waypoints", response_model=WaypointOut, status_code=status.HTTP_201_CREATED
)
def add_waypoint(
    route_id: str,
    payload: WaypointCreate,
    principal: CurrentPrincipal,
    service: RouteServiceDep,
) -> WaypointOut:
    return WaypointOut.model_validate(
        service.add_waypoint(principal, route_id, payload.model_dump())
    )


# --- прогресс семьи ---


@router.post("/{route_id}/progress/start", response_model=ProgressOut)
def start_progress(
    route_id: str, principal: CurrentPrincipal, service: ProgressServiceDep
) -> ProgressOut:
    return ProgressOut.model_validate(service.start(principal, route_id))


@router.get("/{route_id}/progress/me", response_model=ProgressOut | None)
def my_progress(
    route_id: str, principal: CurrentPrincipal, service: ProgressServiceDep
) -> ProgressOut | None:
    progress = service.get_mine(principal, route_id)
    return ProgressOut.model_validate(progress) if progress else None


@router.post("/{route_id}/progress/complete-waypoint", response_model=ProgressOut)
def complete_waypoint(
    route_id: str,
    payload: CompleteWaypointRequest,
    principal: CurrentPrincipal,
    service: ProgressServiceDep,
) -> ProgressOut:
    return ProgressOut.model_validate(
        service.complete_waypoint(principal, route_id, payload.waypoint_id, payload.answer)
    )
