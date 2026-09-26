from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import GuideRating


@dataclass(frozen=True)
class GuideTotals:
    """Оценки одного краеведа за период — сумма, а не среднее: из сумм честно
    складывается и среднее по всем краеведам, и байесовское."""

    guide_id: str
    count: int
    total: int
    last_rated_at: datetime | None


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

    def totals_by_guide(self, since: datetime | None = None) -> list[GuideTotals]:
        """Все краеведы с оценками за период одним GROUP BY. `since=None` — за всё время."""
        stmt = select(
            GuideRating.guide_id,
            func.count(GuideRating.id),
            func.sum(GuideRating.rating),
            func.max(GuideRating.created_at),
        ).group_by(GuideRating.guide_id)
        if since is not None:
            stmt = stmt.where(GuideRating.created_at >= since)
        return [
            GuideTotals(guide_id=guide_id, count=int(count), total=int(total), last_rated_at=last)
            for guide_id, count, total, last in self.db.execute(stmt)
        ]

    def distribution(self, guide_id: str) -> dict[int, int]:
        """Сколько оценок каждого балла. Баллов без оценок в ответе нет."""
        rows = self.db.execute(
            select(GuideRating.rating, func.count(GuideRating.id))
            .where(GuideRating.guide_id == guide_id)
            .group_by(GuideRating.rating)
        )
        return {int(rating): int(count) for rating, count in rows}
