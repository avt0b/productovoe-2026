from fastapi import APIRouter

from api.deps import AchievementServiceDep, CurrentPrincipal
from api.schemas.achievement import AchievementOut

router = APIRouter(prefix="/achievements", tags=["achievements (значки за активность)"])


@router.get("/me", response_model=list[AchievementOut])
def my_achievements(
    principal: CurrentPrincipal, service: AchievementServiceDep
) -> list[AchievementOut]:
    return [AchievementOut.model_validate(a) for a in service.list_for(principal.user_id)]
