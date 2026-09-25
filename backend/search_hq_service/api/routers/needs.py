from typing import Annotated

from fastapi import APIRouter, Query, status

from api.deps import CurrentPrincipal, NeedServiceDep
from api.schemas.need import DonationCreate, DonationOut, DonationPublicOut, NeedOut, NeedUpdate
from core.models import NeedKind, NeedStatus

router = APIRouter(prefix="/needs", tags=["needs (потребности и сборы)"])


@router.get("", response_model=list[NeedOut])
def list_needs(
    service: NeedServiceDep,
    kind: Annotated[NeedKind | None, Query()] = None,
    status_: Annotated[NeedStatus | None, Query(alias="status")] = NeedStatus.open,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[NeedOut]:
    rows = service.search(kind=kind, status=status_, limit=limit, offset=offset)
    return [NeedOut.model_validate(n) for n in rows]


@router.get("/{need_id}", response_model=NeedOut)
def get_need(need_id: str, service: NeedServiceDep) -> NeedOut:
    return NeedOut.model_validate(service.get(need_id))


@router.patch("/{need_id}", response_model=NeedOut)
def update_need(
    need_id: str, payload: NeedUpdate, principal: CurrentPrincipal, service: NeedServiceDep
) -> NeedOut:
    return NeedOut.model_validate(service.update(principal, need_id, payload.to_update_dict()))


@router.post("/{need_id}/close", response_model=NeedOut)
def close_need(need_id: str, principal: CurrentPrincipal, service: NeedServiceDep) -> NeedOut:
    return NeedOut.model_validate(service.close(principal, need_id))


@router.delete("/{need_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_need(need_id: str, principal: CurrentPrincipal, service: NeedServiceDep) -> None:
    service.delete(principal, need_id)


@router.post(
    "/{need_id}/donations", response_model=DonationOut, status_code=status.HTTP_201_CREATED
)
def donate(
    need_id: str,
    payload: DonationCreate,
    principal: CurrentPrincipal,
    service: NeedServiceDep,
) -> DonationOut:
    donation = service.donate(
        principal,
        need_id,
        amount=payload.amount,
        comment=payload.comment,
        return_url=payload.return_url,
    )
    return DonationOut.model_validate(donation)


@router.get("/{need_id}/donations", response_model=list[DonationPublicOut])
def list_donations(need_id: str, service: NeedServiceDep) -> list[DonationPublicOut]:
    # Лента публичная: суммы и комментарии видны всем, а кто именно дал — нет.
    return [DonationPublicOut.model_validate(d) for d in service.donations_for(need_id)]
