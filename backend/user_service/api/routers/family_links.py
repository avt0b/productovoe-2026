from fastapi import APIRouter, status

from api.deps import CurrentPrincipal, FamilyLinkServiceDep
from api.schemas.family_link import FamilyLinkInviteOut, FamilyMemberOut, RedeemRequest

router = APIRouter(prefix="/family-links", tags=["family-links (семья: находить друг друга)"])


@router.post("/invite", response_model=FamilyLinkInviteOut, status_code=status.HTTP_201_CREATED)
def create_invite(
    principal: CurrentPrincipal, service: FamilyLinkServiceDep
) -> FamilyLinkInviteOut:
    return FamilyLinkInviteOut.model_validate(service.create_invite(principal))


@router.post("/redeem", status_code=status.HTTP_204_NO_CONTENT)
def redeem_invite(
    payload: RedeemRequest, principal: CurrentPrincipal, service: FamilyLinkServiceDep
) -> None:
    service.redeem_invite(principal, payload.code)


@router.get("/mine", response_model=list[FamilyMemberOut])
def my_family(
    principal: CurrentPrincipal, service: FamilyLinkServiceDep
) -> list[FamilyMemberOut]:
    return [FamilyMemberOut.model_validate(m) for m in service.list_mine(principal)]


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    member_id: str, principal: CurrentPrincipal, service: FamilyLinkServiceDep
) -> None:
    service.remove(principal, member_id)
