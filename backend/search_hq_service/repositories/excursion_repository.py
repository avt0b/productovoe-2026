from collections.abc import Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import Excursion, ExcursionParticipant, ExcursionStatus, RegistrationStatus

# Экскурсии, на которые ещё можно прийти: запись идёт или группа собирается.
ACTIVE_STATUSES = (ExcursionStatus.scheduled, ExcursionStatus.gathering)


class ExcursionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, excursion_id: str) -> Excursion | None:
        return self.db.get(Excursion, excursion_id)

    def add(self, excursion: Excursion) -> Excursion:
        self.db.add(excursion)
        self.db.flush()
        return excursion

    def search(
        self,
        *,
        upcoming_only: bool = True,
        guide_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Excursion]:
        stmt = select(Excursion)
        if upcoming_only:
            stmt = stmt.where(Excursion.status.in_(ACTIVE_STATUSES))
        if guide_id:
            stmt = stmt.where(Excursion.guide_id == guide_id)
        return self.db.scalars(
            stmt.order_by(Excursion.starts_at.asc()).limit(limit).offset(offset)
        ).all()

    def joined_by(self, user_id: str) -> Sequence[Excursion]:
        return self.db.scalars(
            select(Excursion)
            .join(ExcursionParticipant, ExcursionParticipant.excursion_id == Excursion.id)
            .where(
                ExcursionParticipant.user_id == user_id,
                ExcursionParticipant.status == RegistrationStatus.registered,
            )
            .order_by(Excursion.starts_at.asc())
        ).all()

    # --- участники ---

    def get_participant(self, excursion_id: str, user_id: str) -> ExcursionParticipant | None:
        return self.db.scalar(
            select(ExcursionParticipant).where(
                ExcursionParticipant.excursion_id == excursion_id,
                ExcursionParticipant.user_id == user_id,
            )
        )

    def add_participant(self, participant: ExcursionParticipant) -> ExcursionParticipant:
        self.db.add(participant)
        self.db.flush()
        return participant

    def participants_for(self, excursion_id: str) -> Sequence[ExcursionParticipant]:
        return self.db.scalars(
            select(ExcursionParticipant)
            .where(ExcursionParticipant.excursion_id == excursion_id)
            .order_by(ExcursionParticipant.created_at.asc())
        ).all()

    def checked_in_for(self, excursion_id: str) -> Sequence[ExcursionParticipant]:
        return self.db.scalars(
            select(ExcursionParticipant)
            .where(
                ExcursionParticipant.excursion_id == excursion_id,
                ExcursionParticipant.status == RegistrationStatus.registered,
                ExcursionParticipant.checked_in_at.is_not(None),
            )
            .order_by(ExcursionParticipant.checked_in_at.asc())
        ).all()

    def count_registered(self, excursion_id: str) -> int:
        return self.counts([excursion_id]).get(excursion_id, (0, 0))[0]

    def count_checked_in(self, excursion_id: str) -> int:
        return self.counts([excursion_id]).get(excursion_id, (0, 0))[1]

    def counts(self, excursion_ids: Iterable[str]) -> dict[str, tuple[int, int]]:
        """Сколько записано и сколько уже пришло — одним запросом на всю страницу списка."""
        ids = list(excursion_ids)
        if not ids:
            return {}
        rows = self.db.execute(
            select(
                ExcursionParticipant.excursion_id,
                func.count(ExcursionParticipant.id),
                func.count(ExcursionParticipant.checked_in_at),
            )
            .where(
                ExcursionParticipant.excursion_id.in_(ids),
                ExcursionParticipant.status == RegistrationStatus.registered,
            )
            .group_by(ExcursionParticipant.excursion_id)
        )
        return {
            excursion_id: (registered, checked_in) for excursion_id, registered, checked_in in rows
        }

    def participations(
        self, user_id: str, excursion_ids: Iterable[str]
    ) -> dict[str, ExcursionParticipant]:
        """Записи одного человека на несколько экскурсий — чтобы список знал, куда он записан."""
        ids = list(excursion_ids)
        if not ids:
            return {}
        rows = self.db.scalars(
            select(ExcursionParticipant).where(
                ExcursionParticipant.user_id == user_id,
                ExcursionParticipant.excursion_id.in_(ids),
            )
        ).all()
        return {row.excursion_id: row for row in rows}
