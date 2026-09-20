from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import RegistrationStatus, TripRegistration, VolunteerTrip


class TripRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, trip_id: str) -> VolunteerTrip | None:
        return self.db.get(VolunteerTrip, trip_id)

    def add(self, trip: VolunteerTrip) -> VolunteerTrip:
        self.db.add(trip)
        self.db.flush()
        return trip

    def search(
        self,
        *,
        squad_id: str | None = None,
        upcoming_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[VolunteerTrip]:
        stmt = select(VolunteerTrip)
        if squad_id:
            stmt = stmt.where(VolunteerTrip.squad_id == squad_id)
        if upcoming_only:
            stmt = stmt.where(VolunteerTrip.starts_on >= datetime.now(UTC).date())
        return self.db.scalars(
            stmt.order_by(VolunteerTrip.starts_on.asc()).limit(limit).offset(offset)
        ).all()

    # --- регистрации ---

    def get_registration(self, trip_id: str, user_id: str) -> TripRegistration | None:
        return self.db.scalar(
            select(TripRegistration).where(
                TripRegistration.trip_id == trip_id, TripRegistration.user_id == user_id
            )
        )

    def add_registration(self, reg: TripRegistration) -> TripRegistration:
        self.db.add(reg)
        self.db.flush()
        return reg

    def count_active_registrations(self, trip_id: str) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(TripRegistration)
                .where(
                    TripRegistration.trip_id == trip_id,
                    TripRegistration.status == RegistrationStatus.registered,
                )
            )
            or 0
        )

    def registrations_for(self, trip_id: str) -> Sequence[TripRegistration]:
        return self.db.scalars(
            select(TripRegistration)
            .where(TripRegistration.trip_id == trip_id)
            .order_by(TripRegistration.created_at.asc())
        ).all()
