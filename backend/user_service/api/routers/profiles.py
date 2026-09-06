from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.deps import CurrentPrincipal, ProfileServiceDep, require_root
from api.schemas.profile import ProfileOut, ProfileUpdate, VerifyRequest

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileOut)
def get_my_profile(principal: CurrentPrincipal, service: ProfileServiceDep) -> ProfileOut:
    return ProfileOut.model_validate(service.get_or_create_own(principal))


@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate, principal: CurrentPrincipal, service: ProfileServiceDep
) -> ProfileOut:
    return ProfileOut.model_validate(service.update_own(principal, payload.to_update_dict()))


@router.get("", response_model=list[ProfileOut], dependencies=[Depends(require_root)])
def list_profiles(
    service: ProfileServiceDep,
    role: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProfileOut]:
    rows = service.search(role=role, limit=limit, offset=offset)
    return [ProfileOut.model_validate(p) for p in rows]


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(
    profile_id: str, _: CurrentPrincipal, service: ProfileServiceDep
) -> ProfileOut:
    return ProfileOut.model_validate(service.get(profile_id))


@router.patch("/{profile_id}/verify", response_model=ProfileOut)
def verify_profile(
    profile_id: str,
    payload: VerifyRequest,
    principal: CurrentPrincipal,
    service: ProfileServiceDep,
) -> ProfileOut:
    return ProfileOut.model_validate(
        service.set_verified(principal, profile_id, payload.is_verified)
    )
