from fastapi import APIRouter, status

from api.deps import CurrentPrincipal, FamilyHeroServiceDep
from api.schemas.family_hero import FamilyHeroCreate, FamilyHeroOut, FamilyHeroUpdate

router = APIRouter(prefix="/family-heroes", tags=["family-heroes (семейное древо)"])


@router.get("/mine", response_model=list[FamilyHeroOut])
def my_heroes(principal: CurrentPrincipal, service: FamilyHeroServiceDep) -> list[FamilyHeroOut]:
    return [FamilyHeroOut.model_validate(h) for h in service.for_owner(principal.user_id)]


@router.post("", response_model=FamilyHeroOut, status_code=status.HTTP_201_CREATED)
def create_hero(
    payload: FamilyHeroCreate, principal: CurrentPrincipal, service: FamilyHeroServiceDep
) -> FamilyHeroOut:
    return FamilyHeroOut.model_validate(service.create(principal, payload.model_dump()))


@router.patch("/{hero_id}", response_model=FamilyHeroOut)
def update_hero(
    hero_id: str,
    payload: FamilyHeroUpdate,
    principal: CurrentPrincipal,
    service: FamilyHeroServiceDep,
) -> FamilyHeroOut:
    return FamilyHeroOut.model_validate(
        service.update(principal, hero_id, payload.to_update_dict())
    )


@router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hero(hero_id: str, principal: CurrentPrincipal, service: FamilyHeroServiceDep) -> None:
    service.delete(principal, hero_id)
