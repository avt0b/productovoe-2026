from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import GuideRating


class RatingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_rater(self, excursion_id: str, rater_id: str) -> GuideRating | None:
        return self.db.scalar(
            select(GuideRating).where(
                GuideRating.excursion_id == excursion_id,
                GuideRating.rater_id == rater_id,
            )
        )

    def add(self, rating: GuideRating) -> GuideRating:
        self.db.add(rating)
        self.db.flush()
        return rating

    def for_excursion(self, excursion_id: str, *, limit: int = 200) -> Sequence[GuideRating]:
        return self.db.scalars(
            select(GuideRating)
            .where(GuideRating.excursion_id == excursion_id)
            .order_by(GuideRating.created_at.desc())
            .limit(limit)
        ).all()

    def summary_for_guide(self, guide_id: str) -> tuple[float, int]:
        avg, count = self.db.execute(
            select(func.avg(GuideRating.rating), func.count(GuideRating.id)).where(
                GuideRating.guide_id == guide_id
            )
        ).one()
        return (round(float(avg), 2) if avg is not None else 0.0, int(count or 0))

    def recent_for_guide(self, guide_id: str, *, limit: int = 20) -> Sequence[GuideRating]:
        return self.db.scalars(
            select(GuideRating)
            .where(GuideRating.guide_id == guide_id)
            .order_by(GuideRating.created_at.desc())
            .limit(limit)
        ).all()
