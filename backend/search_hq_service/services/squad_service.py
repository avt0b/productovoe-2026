from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import NotFound, PermissionDenied
from core.models import Squad
from core.security import Principal
from repositories.squad_repository import SquadRepository
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
        if not can_create_squad(principal):
            raise PermissionDenied("Создавать отряды могут поисковики и модераторы")
        squad = self.repo.add(Squad(leader_id=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(squad)
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
        self.repo.delete(squad)
        self.db.commit()

    @staticmethod
    def _ensure_can_manage(principal: Principal, squad: Squad) -> None:
        if is_staff(principal) or squad.leader_id == principal.user_id:
            return
        raise PermissionDenied("Управлять отрядом может его командир или модератор")
