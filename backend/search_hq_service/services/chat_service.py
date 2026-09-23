from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import ContentRejected, NotFound, PermissionDenied
from core.models import ChatMessage, ChatSubjectType, Excursion, RegistrationStatus, VolunteerTrip
from core.security import Principal
from repositories.chat_repository import ChatRepository
from repositories.excursion_repository import ExcursionRepository
from repositories.squad_repository import SquadRepository
from repositories.trip_repository import TripRepository
from services import moderation
from services.permissions import is_staff


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ChatRepository(db)
        self.trips = TripRepository(db)
        self.squads = SquadRepository(db)
        self.excursions = ExcursionRepository(db)

    # --- выезд «Выходные с поисковиком» ---

    def trip_messages(
        self, principal: Principal, trip_id: str, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ChatMessage]:
        trip = self._get_trip(trip_id)
        self._ensure_trip_member(principal, trip)
        return self.repo.list_for(ChatSubjectType.trip, trip_id, limit=limit, offset=offset)

    def post_trip_message(self, principal: Principal, trip_id: str, body: str) -> ChatMessage:
        trip = self._get_trip(trip_id)
        self._ensure_trip_member(principal, trip)
        if moderation.contains_banned_content(body):
            raise ContentRejected()
        message = self.repo.add(
            ChatMessage(
                subject_type=ChatSubjectType.trip,
                subject_id=trip_id,
                author_id=principal.user_id,
                body=body,
            )
        )
        self.db.commit()
        self.db.refresh(message)
        return message

    # --- экскурсии краеведов ---

    def excursion_messages(
        self, principal: Principal, excursion_id: str, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ChatMessage]:
        excursion = self._get_excursion(excursion_id)
        self._ensure_excursion_member(principal, excursion)
        return self.repo.list_for(ChatSubjectType.excursion, excursion_id, limit=limit, offset=offset)

    def post_excursion_message(
        self, principal: Principal, excursion_id: str, body: str
    ) -> ChatMessage:
        excursion = self._get_excursion(excursion_id)
        self._ensure_excursion_member(principal, excursion)
        if moderation.contains_banned_content(body):
            raise ContentRejected()
        message = self.repo.add(
            ChatMessage(
                subject_type=ChatSubjectType.excursion,
                subject_id=excursion_id,
                author_id=principal.user_id,
                body=body,
            )
        )
        self.db.commit()
        self.db.refresh(message)
        return message

    # --- helpers ---

    def _get_trip(self, trip_id: str) -> VolunteerTrip:
        trip = self.trips.get(trip_id)
        if trip is None:
            raise NotFound("Выезд не найден")
        return trip

    def _get_excursion(self, excursion_id: str) -> Excursion:
        excursion = self.excursions.get(excursion_id)
        if excursion is None:
            raise NotFound("Экскурсия не найдена")
        return excursion

    def _ensure_trip_member(self, principal: Principal, trip: VolunteerTrip) -> None:
        squad = self.squads.get(trip.squad_id)
        leader_id = squad.leader_id if squad else ""
        if is_staff(principal) or leader_id == principal.user_id:
            return
        reg = self.trips.get_registration(trip.id, principal.user_id)
        if reg is not None and reg.status is RegistrationStatus.registered:
            return
        raise PermissionDenied("Чат доступен записавшимся волонтёрам и командиру отряда")

    def _ensure_excursion_member(self, principal: Principal, excursion: Excursion) -> None:
        if is_staff(principal) or excursion.guide_id == principal.user_id:
            return
        participant = self.excursions.get_participant(excursion.id, principal.user_id)
        if participant is not None and participant.status is RegistrationStatus.registered:
            return
        raise PermissionDenied("Чат доступен записавшимся и краеведу")
