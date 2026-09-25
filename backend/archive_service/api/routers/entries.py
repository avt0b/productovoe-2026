from typing import Annotated, Literal

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, EntryServiceDep, OptionalPrincipal
from api.schemas.entry import (
    EntryCreate,
    EntryNearbyOut,
    EntryOut,
    EntryPublicOut,
    EntrySummaryOut,
    EntryUpdate,
    ReviewRequest,
)
from core.models import EntryKind, EntryStatus
from services.entry_service import VERIFIER_ROLES

router = APIRouter(prefix="/entries", tags=["entries (народный архив)"])


@router.get("", response_model=list[EntryPublicOut])
def list_entries(
    service: EntryServiceDep,
    kind: Annotated[EntryKind | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    point_id: Annotated[str | None, Query(max_length=36)] = None,
    poi_id: Annotated[str | None, Query(max_length=36)] = None,
    prefix: Annotated[str | None, Query(max_length=32)] = None,
    sort: Annotated[Literal["new", "title"], Query()] = "new",
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EntryPublicOut]:
    """Публичная лента — только подтверждённые записи, без служебной заметки модератора.
    С `point_id`/`poi_id` — записи, привязанные к конкретной точке карты (карточка точки).
    `prefix` — заголовок начинается с этих букв (алфавит Книги памяти), `sort=title` — по алфавиту."""
    rows = service.search_public(
        kind=kind,
        q=q,
        point_id=point_id,
        poi_id=poi_id,
        prefix=prefix,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return [EntryPublicOut.model_validate(e) for e in rows]


@router.get("/summary", response_model=EntrySummaryOut)
def entries_summary(
    service: EntryServiceDep,
    kind: Annotated[EntryKind | None, Query()] = None,
) -> EntrySummaryOut:
    """Сводка по подтверждённым записям раздела: сколько имён, у скольких известна
    дата и точка на карте, с каких букв начинаются заголовки."""
    return EntrySummaryOut(**service.summary_public(kind=kind))


@router.get("/nearby-pending", response_model=list[EntryNearbyOut])
def nearby_pending_entries(
    service: EntryServiceDep,
    min_lat: Annotated[float, Query(ge=-90, le=90)],
    min_lon: Annotated[float, Query(ge=-180, le=180)],
    max_lat: Annotated[float, Query(ge=-90, le=90)],
    max_lon: Annotated[float, Query(ge=-180, le=180)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[EntryNearbyOut]:
    """Неподтверждённые записи в прямоугольнике — витрина для подсказки «рядом есть
    неподтверждённая заметка, помоги проверить» в семейном навигаторе (route_service).
    Без авторизации и без прав верификатора: только id/kind/title/координаты."""
    rows = service.search_nearby_pending(bbox=(min_lat, min_lon, max_lat, max_lon), limit=limit)
    return [EntryNearbyOut.model_validate(e) for e in rows]


@router.get("/moderation", response_model=list[EntryOut])
def moderation_queue(
    principal: CurrentPrincipal,
    service: EntryServiceDep,
    status_: Annotated[EntryStatus, Query(alias="status")] = EntryStatus.pending,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EntryOut]:
    rows = service.search_moderation(principal, status=status_, limit=limit, offset=offset)
    return [EntryOut.model_validate(e) for e in rows]


@router.get("/mine", response_model=list[EntryOut])
def my_entries(
    principal: CurrentPrincipal,
    service: EntryServiceDep,
    status_: Annotated[EntryStatus | None, Query(alias="status")] = None,
) -> list[EntryOut]:
    rows = service.list_mine(principal, status=status_)
    return [EntryOut.model_validate(e) for e in rows]


@router.post("", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: EntryCreate, principal: CurrentPrincipal, service: EntryServiceDep
) -> EntryOut:
    return EntryOut.model_validate(service.create(principal, payload.model_dump()))


@router.get("/{entry_id}")
def get_entry(
    entry_id: str, principal: OptionalPrincipal, service: EntryServiceDep
) -> EntryOut | EntryPublicOut:
    entry = service.get_visible(principal, entry_id)
    privileged = principal is not None and (
        principal.is_root
        or principal.role in VERIFIER_ROLES
        or entry.submitted_by == principal.user_id
    )
    if privileged:
        return EntryOut.model_validate(entry)
    return EntryPublicOut.model_validate(entry)


@router.patch("/{entry_id}", response_model=EntryOut)
def update_entry(
    entry_id: str,
    payload: EntryUpdate,
    principal: CurrentPrincipal,
    service: EntryServiceDep,
) -> EntryOut:
    return EntryOut.model_validate(service.update(principal, entry_id, payload.to_update_dict()))


@router.post("/{entry_id}/verify", response_model=EntryOut)
def verify_entry(
    entry_id: str,
    payload: ReviewRequest,
    principal: CurrentPrincipal,
    service: EntryServiceDep,
) -> EntryOut:
    return EntryOut.model_validate(service.verify(principal, entry_id, note=payload.note))


@router.post("/{entry_id}/reject", response_model=EntryOut)
def reject_entry(
    entry_id: str,
    payload: ReviewRequest,
    principal: CurrentPrincipal,
    service: EntryServiceDep,
) -> EntryOut:
    return EntryOut.model_validate(service.reject(principal, entry_id, note=payload.note))


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: str, principal: CurrentPrincipal, service: EntryServiceDep) -> None:
    service.delete(principal, entry_id)
