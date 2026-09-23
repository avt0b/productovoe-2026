from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import ExcursionStatus, GuideRating
from core.security import Principal
from repositories.excursion_repository import ExcursionRepository
from repositories.rating_repository import RatingRepository


class RatingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RatingRepository(db)
        self.excursions = ExcursionRepository(db)

    def rate(
        self, principal: Principal, excursion_id: str, *, rating: int, comment: str
    ) -> GuideRating:
        excursion = self.excursions.get(excursion_id)
        if excursion is None:
            raise NotFound("Экскурсия не найдена")
        if excursion.guide_id == principal.user_id:
            raise Conflict("Краевед не оценивает свою экскурсию")
        if excursion.status is not ExcursionStatus.finished:
            raise Conflict("Оценить можно только завершённую экскурсию")

        participant = self.excursions.get_participant(excursion_id, principal.user_id)
        if participant is None or participant.checked_in_at is None:
            raise PermissionDenied("Оценивать может только участник, который реально пришёл")

        existing = self.repo.get_by_rater(excursion_id, principal.user_id)
        if existing is not None:
            existing.rating = rating
            existing.comment = comment
            self.db.commit()
            self.db.refresh(existing)
            return existing

        created = self.repo.add(
            GuideRating(
                excursion_id=excursion_id,
                guide_id=excursion.guide_id,
                rater_id=principal.user_id,
                rating=rating,
                comment=comment,
            )
        )
        self.db.commit()
        self.db.refresh(created)
        return created

    def for_excursion(self, excursion_id: str) -> list[GuideRating]:
        if self.excursions.get(excursion_id) is None:
            raise NotFound("Экскурсия не найдена")
        return list(self.repo.for_excursion(excursion_id))

    def guide_summary(self, guide_id: str) -> tuple[float, int, list[GuideRating]]:
        average, count = self.repo.summary_for_guide(guide_id)
        recent = self.repo.recent_for_guide(guide_id)
        return average, count, list(recent)
