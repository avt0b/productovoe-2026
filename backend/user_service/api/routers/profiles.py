from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.deps import (
    AchievementServiceDep,
    CurrentPrincipal,
    FamilyHeroServiceDep,
    ProfileServiceDep,
    StatsServiceDep,
    require_root,
)
from api.schemas.achievement import AchievementOut
from api.schemas.family_hero import FamilyHeroOut
from api.schemas.profile import ProfileOut, ProfileUpdate, VerifyRequest
from core.models import Profile
from services.achievement_service import AchievementService
from services.family_hero_service import FamilyHeroService
from services.stats_service import StatsService

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _full_profile(
    profile: Profile,
    achievements: AchievementService,
    stats: StatsService,
    heroes: FamilyHeroService,
) -> ProfileOut:
    badges = [AchievementOut.model_validate(a) for a in achievements.list_for(profile.id)]
    by_metric = stats.for_user(profile.id)
    family = [FamilyHeroOut.model_validate(h) for h in heroes.for_owner(profile.id)]
    return ProfileOut.model_validate(profile).model_copy(
        update={
            "achievements": badges,
            "routes_completed": by_metric.get("routes_completed", 0),
            "excursions_completed": by_metric.get("excursions_completed", 0),
            "finds_count": by_metric.get("finds_count", 0),
            "heroes": family,
        }
    )


@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    principal: CurrentPrincipal,
    service: ProfileServiceDep,
    achievements: AchievementServiceDep,
    stats: StatsServiceDep,
    heroes: FamilyHeroServiceDep,
) -> ProfileOut:
    return _full_profile(service.get_or_create_own(principal), achievements, stats, heroes)


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
    profile_id: str,
    _: CurrentPrincipal,
    service: ProfileServiceDep,
    achievements: AchievementServiceDep,
    stats: StatsServiceDep,
    heroes: FamilyHeroServiceDep,
) -> ProfileOut:
    return _full_profile(service.get(profile_id), achievements, stats, heroes)


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
