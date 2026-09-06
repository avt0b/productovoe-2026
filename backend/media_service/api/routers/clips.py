from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import ClipServiceDep, CurrentPrincipal, OptionalPrincipal
from api.schemas.clip import (
    ClipCreate,
    ClipOut,
    ClipUpdate,
    ShareCreate,
    ShareOut,
)
from core.models import ClipStatus

router = APIRouter(prefix="/clips", tags=["clips (Живое фото)"])


@router.get("", response_model=list[ClipOut])
def public_gallery(
    service: ClipServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ClipOut]:
    """Общий мемориал приложения — только публичные готовые клипы."""
    return [ClipOut.model_validate(c) for c in service.public_gallery(limit=limit, offset=offset)]


@router.get("/mine", response_model=list[ClipOut])
def my_clips(
    principal: CurrentPrincipal,
    service: ClipServiceDep,
    status_: Annotated[ClipStatus | None, Query(alias="status")] = None,
) -> list[ClipOut]:
    return [ClipOut.model_validate(c) for c in service.list_mine(principal, status=status_)]


@router.post("", response_model=ClipOut, status_code=status.HTTP_201_CREATED)
def create_clip(
    payload: ClipCreate, principal: CurrentPrincipal, service: ClipServiceDep
) -> ClipOut:
    return ClipOut.model_validate(service.create(principal, payload.model_dump()))


@router.get("/{clip_id}", response_model=ClipOut)
def get_clip(
    clip_id: str, principal: OptionalPrincipal, service: ClipServiceDep
) -> ClipOut:
    return ClipOut.model_validate(service.get_visible(principal, clip_id))


@router.patch("/{clip_id}", response_model=ClipOut)
def update_clip(
    clip_id: str, payload: ClipUpdate, principal: CurrentPrincipal, service: ClipServiceDep
) -> ClipOut:
    return ClipOut.model_validate(
        service.update(principal, clip_id, payload.to_update_dict())
    )


@router.post("/{clip_id}/retry", response_model=ClipOut)
def retry_clip(clip_id: str, principal: CurrentPrincipal, service: ClipServiceDep) -> ClipOut:
    return ClipOut.model_validate(service.retry(principal, clip_id))


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clip(clip_id: str, principal: CurrentPrincipal, service: ClipServiceDep) -> None:
    service.delete(principal, clip_id)


# --- «Отправить родным» ---

@router.post("/{clip_id}/shares", response_model=ShareOut, status_code=status.HTTP_201_CREATED)
def share_clip(
    clip_id: str, payload: ShareCreate, principal: CurrentPrincipal, service: ClipServiceDep
) -> ShareOut:
    share = service.share(
        principal, clip_id, recipient=payload.recipient, note=payload.note
    )
    return ShareOut.model_validate(share)


@router.get("/{clip_id}/shares", response_model=list[ShareOut])
def list_shares(
    clip_id: str, principal: CurrentPrincipal, service: ClipServiceDep
) -> list[ShareOut]:
    return [ShareOut.model_validate(s) for s in service.shares_of(principal, clip_id)]
