from typing import Annotated, Literal

from fastapi import APIRouter, Query

from api.deps import OptionalPrincipal, RatingServiceDep
from api.schemas.rating import GuideLeaderboardOut, GuideRatingSummaryOut

router = APIRouter(prefix="/guides", tags=["guides (рейтинг гидов)"])


@router.get("/rating", response_model=GuideLeaderboardOut)
def guides_leaderboard(
    service: RatingServiceDep,
    principal: OptionalPrincipal,
    period: Annotated[Literal["all", "month"], Query()] = "all",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GuideLeaderboardOut:
    """Рейтинг краеведов. Публичный: выбирать, к кому идти, можно и без входа;
    с токеном своя строка помечена `is_me`."""
    board = service.leaderboard(principal, period=period, limit=limit, offset=offset)
    return GuideLeaderboardOut.from_view(board)


@router.get("/{guide_id}/rating", response_model=GuideRatingSummaryOut)
def guide_rating(guide_id: str, service: RatingServiceDep) -> GuideRatingSummaryOut:
    return GuideRatingSummaryOut.from_view(service.guide_card(guide_id))
