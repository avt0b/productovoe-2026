from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import RegistrationStatus, TripRegistration, VolunteerTrip
from core.security import Principal
from repositories.squad_repository import SquadRepository
from repositories.trip_repository import TripRepository
from services.achievement_client import award_achievement
from services.permissions import is_staff

ACHIEVEMENT_TRIP_VOLUNTEER = "trip_volunteer"


class TripService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TripRepository(db)
        self.squads = SquadRepository(db)

    def get(self, trip_id: str) -> VolunteerTrip:
        trip = self.repo.get(trip_id)
        if trip is None:
            raise NotFound("Выезд не найден")
        return trip

    def search(self, **filters) -> Sequence[VolunteerTrip]:
        return self.repo.search(**filters)

    def create(self, principal: Principal, squad_id: str, data: dict) -> VolunteerTrip:
        squad = self.squads.get(squad_id)
        if squad is None:
            raise NotFound("Отряд не найден")
        self._ensure_manager(principal, squad.leader_id)
        trip = self.repo.add(VolunteerTrip(squad_id=squad_id, **data))
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def update(self, principal: Principal, trip_id: str, data: dict) -> VolunteerTrip:
        trip = self.get(trip_id)
        self._ensure_manager(principal, self._leader_of(trip))
        if "capacity" in data and data["capacity"] < self.repo.count_active_registrations(trip_id):
            raise Conflict("Мест не может быть меньше, чем уже записалось")
        for field, value in data.items():
            setattr(trip, field, value)
        self.db.commit()
        self.db.refresh(trip)
        return trip

    # --- регистрации волонтёров ---

    def register(self, principal: Principal, trip_id: str) -> TripRegistration:
        trip = self.get(trip_id)
        existing = self.repo.get_registration(trip_id, principal.user_id)
        if existing and existing.status is RegistrationStatus.registered:
            return existing

        if self.repo.count_active_registrations(trip_id) >= trip.capacity:
            raise Conflict("Все места заняты")

        if existing:
            existing.status = RegistrationStatus.registered
            reg = existing
        else:
            reg = self.repo.add_registration(
                TripRegistration(trip_id=trip_id, user_id=principal.user_id)
            )
        self.db.commit()
        self.db.refresh(reg)
        award_achievement(user_id=principal.user_id, code=ACHIEVEMENT_TRIP_VOLUNTEER)
        return reg

    def cancel(self, principal: Principal, trip_id: str) -> None:
        reg = self.repo.get_registration(trip_id, principal.user_id)
        if reg is None or reg.status is RegistrationStatus.cancelled:
            raise NotFound("Регистрация не найдена")
        reg.status = RegistrationStatus.cancelled
        self.db.commit()

    def mine(self, principal: Principal, *, upcoming_only: bool) -> Sequence[VolunteerTrip]:
        """Выезды, на которые человек записан, — чтобы приложение показало «Вы записаны»."""
        return self.repo.trips_of_volunteer(principal.user_id, upcoming_only=upcoming_only)

    def registrations_for(self, principal: Principal, trip_id: str) -> Sequence[TripRegistration]:
        trip = self.get(trip_id)
        self._ensure_manager(principal, self._leader_of(trip))
        return self.repo.registrations_for(trip_id)

    # --- helpers ---

    def _leader_of(self, trip: VolunteerTrip) -> str:
        squad = self.squads.get(trip.squad_id)
        return squad.leader_id if squad else ""

    @staticmethod
    def _ensure_manager(principal: Principal, leader_id: str) -> None:
        if is_staff(principal) or leader_id == principal.user_id:
            return
        raise PermissionDenied("Управлять выездом может командир отряда или модератор")
