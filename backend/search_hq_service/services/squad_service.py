from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import NotFound, PermissionDenied
from core.models import ChatSubjectType, Squad, SquadKind
from core.security import Principal
from repositories.chat_repository import ChatRepository
from repositories.squad_repository import SquadRepository
from services import achievement_client
from services.permissions import can_create_squad, is_staff


class SquadService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SquadRepository(db)

    def get(self, squad_id: str) -> Squad:
        squad = self.repo.get(squad_id)
        if squad is None:
            raise NotFound("Отряд не найден")
        return squad

    def search(self, **filters) -> Sequence[Squad]:
        return self.repo.search(**filters)

    def create(self, principal: Principal, data: dict) -> Squad:
        if not can_create_squad(principal, data.get("kind", SquadKind.squad)):
            raise PermissionDenied(
                "Отряд заводит поисковик, музей и школу — поисковик или краевед"
            )
        squad = self.repo.add(Squad(leader_id=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(squad)
        if squad.kind is SquadKind.squad:
            achievement_client.award_achievement(
                user_id=principal.user_id, code=achievement_client.SEARCHER_SQUAD_FOUNDER
            )
        return squad

    def update(self, principal: Principal, squad_id: str, data: dict) -> Squad:
        squad = self.get(squad_id)
        self._ensure_can_manage(principal, squad)
        for field, value in data.items():
            setattr(squad, field, value)
        self.db.commit()
        self.db.refresh(squad)
        return squad

    def delete(self, principal: Principal, squad_id: str) -> None:
        squad = self.get(squad_id)
        self._ensure_can_manage(principal, squad)
        # Сборы и выезды уходят каскадом, а у переписки выездов внешнего ключа нет.
        ChatRepository(self.db).delete_for(ChatSubjectType.trip, [trip.id for trip in squad.trips])
        self.repo.delete(squad)
        self.db.commit()

    @staticmethod
    def _ensure_can_manage(principal: Principal, squad: Squad) -> None:
        if is_staff(principal) or squad.leader_id == principal.user_id:
            return
        raise PermissionDenied("Управлять отрядом может его командир или модератор")
