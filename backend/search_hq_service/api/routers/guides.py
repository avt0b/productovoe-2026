from fastapi import APIRouter

from api.deps import RatingServiceDep
from api.schemas.rating import GuideRatingOut, GuideRatingSummaryOut

router = APIRouter(prefix="/guides", tags=["guides (рейтинг гидов)"])


@router.get("/{guide_id}/rating", response_model=GuideRatingSummaryOut)
def guide_rating(guide_id: str, service: RatingServiceDep) -> GuideRatingSummaryOut:
    average, count, recent = service.guide_summary(guide_id)
    return GuideRatingSummaryOut(
        guide_id=guide_id,
        average=average,
        count=count,
        recent=[GuideRatingOut.model_validate(r) for r in recent],
    )
