from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, EntryServiceDep, OptionalPrincipal
from api.schemas.entry import EntryCreate, EntryOut, EntryUpdate, ReviewRequest
from core.models import EntryKind, EntryStatus

router = APIRouter(prefix="/entries", tags=["entries (народный архив)"])


@router.get("", response_model=list[EntryOut])
def list_entries(
    service: EntryServiceDep,
    kind: Annotated[EntryKind | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EntryOut]:
    """Публичная лента — только подтверждённые записи."""
    rows = service.search_public(kind=kind, q=q, limit=limit, offset=offset)
    return [EntryOut.model_validate(e) for e in rows]


@router.get("/moderation", response_model=list[EntryOut])
def moderation_queue(
    principal: CurrentPrincipal,
    service: EntryServiceDep,
    status_: Annotated[EntryStatus, Query(alias="status")] = EntryStatus.pending,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EntryOut]:
    rows = service.search_moderation(
        principal, status=status_, limit=limit, offset=offset
    )
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


@router.get("/{entry_id}", response_model=EntryOut)
def get_entry(
    entry_id: str, principal: OptionalPrincipal, service: EntryServiceDep
) -> EntryOut:
    return EntryOut.model_validate(service.get_visible(principal, entry_id))


@router.patch("/{entry_id}", response_model=EntryOut)
def update_entry(
    entry_id: str,
    payload: EntryUpdate,
    principal: CurrentPrincipal,
    service: EntryServiceDep,
) -> EntryOut:
    return EntryOut.model_validate(
        service.update(principal, entry_id, payload.to_update_dict())
    )


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
def delete_entry(
    entry_id: str, principal: CurrentPrincipal, service: EntryServiceDep
) -> None:
    service.delete(principal, entry_id)
