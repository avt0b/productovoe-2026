from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import Donation, NeedKind, NeedStatus, SquadNeed
from core.security import Principal
from repositories.need_repository import NeedRepository
from repositories.squad_repository import SquadRepository
from services.permissions import is_staff


class NeedService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NeedRepository(db)
        self.squads = SquadRepository(db)

    def get(self, need_id: str) -> SquadNeed:
        need = self.repo.get(need_id)
        if need is None:
            raise NotFound("Потребность не найдена")
        return need

    def search(self, **filters) -> Sequence[SquadNeed]:
        return self.repo.search(**filters)

    def create(self, principal: Principal, squad_id: str, data: dict) -> SquadNeed:
        squad = self.squads.get(squad_id)
        if squad is None:
            raise NotFound("Отряд не найден")
        self._ensure_squad_manager(principal, squad.leader_id)
        need = self.repo.add(SquadNeed(squad_id=squad_id, **data))
        self.db.commit()
        self.db.refresh(need)
        return need

    def update(self, principal: Principal, need_id: str, data: dict) -> SquadNeed:
        need = self.get(need_id)
        self._ensure_squad_manager(principal, self._leader_of(need))
        for field, value in data.items():
            setattr(need, field, value)
        self.db.commit()
        self.db.refresh(need)
        return need

    def close(self, principal: Principal, need_id: str) -> SquadNeed:
        need = self.get(need_id)
        self._ensure_squad_manager(principal, self._leader_of(need))
        need.status = NeedStatus.closed
        self.db.commit()
        self.db.refresh(need)
        return need

    def donate(
        self, principal: Principal, need_id: str, *, amount: int, comment: str
    ) -> Donation:
        need = self.get(need_id)
        if need.status is NeedStatus.closed:
            raise Conflict("Сбор закрыт")
        if need.kind is not NeedKind.funds:
            raise Conflict("Взносы принимает только денежный сбор")
        donation = self.repo.add_donation(
            Donation(need_id=need_id, donor_id=principal.user_id, amount=amount, comment=comment)
        )
        need.collected_amount += amount
        if need.target_amount is not None and need.collected_amount >= need.target_amount:
            need.status = NeedStatus.closed
        self.db.commit()
        self.db.refresh(donation)
        return donation

    def donations_for(self, need_id: str) -> Sequence[Donation]:
        self.get(need_id)
        return self.repo.donations_for(need_id)

    # --- helpers ---

    def _leader_of(self, need: SquadNeed) -> str:
        squad = self.squads.get(need.squad_id)
        return squad.leader_id if squad else ""

    @staticmethod
    def _ensure_squad_manager(principal: Principal, leader_id: str) -> None:
        if is_staff(principal) or leader_id == principal.user_id:
            return
        raise PermissionDenied("Управлять потребностями может командир отряда или модератор")
