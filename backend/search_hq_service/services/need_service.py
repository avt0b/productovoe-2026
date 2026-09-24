from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import Donation, DonationStatus, NeedKind, NeedStatus, SquadNeed
from core.security import Principal
from repositories.need_repository import NeedRepository
from repositories.squad_repository import SquadRepository
from services.achievement_client import award_achievement
from services.payment_gateway import get_gateway
from services.permissions import is_staff

ACHIEVEMENT_DONOR = "donor"


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

    def delete(self, principal: Principal, need_id: str) -> None:
        need = self.get(need_id)
        self._ensure_squad_manager(principal, self._leader_of(need))
        if self.repo.has_succeeded_donations(need_id):
            raise Conflict("В сбор уже поступили взносы — его можно только закрыть")
        self.repo.delete(need)
        self.db.commit()

    def donate(
        self,
        principal: Principal,
        need_id: str,
        *,
        amount: int,
        comment: str,
        return_url: str | None = None,
    ) -> Donation:
        need = self.get(need_id)
        if need.status is NeedStatus.closed:
            raise Conflict("Сбор закрыт")
        if need.kind is not NeedKind.funds:
            raise Conflict("Взносы принимает только денежный сбор")

        gateway = get_gateway()
        if gateway is None:
            # Без платёжного шлюза донат учитывается сразу — как было до интеграции ЮKassa.
            donation = self.repo.add_donation(
                Donation(
                    need_id=need_id,
                    donor_id=principal.user_id,
                    amount=amount,
                    comment=comment,
                    status=DonationStatus.succeeded,
                )
            )
            self._credit(need, amount)
            self.db.commit()
            self.db.refresh(donation)
            award_achievement(user_id=principal.user_id, code=ACHIEVEMENT_DONOR)
            return donation

        # С шлюзом донат висит pending, пока ЮKassa не подтвердит платёж.
        payment = gateway.create_payment(
            amount_rub=amount,
            description=f"Взнос в сбор «{need.title}»",
            return_url=return_url or settings.yookassa_return_url,
            metadata={"need_id": need_id, "donor_id": principal.user_id},
        )
        donation = self.repo.add_donation(
            Donation(
                need_id=need_id,
                donor_id=principal.user_id,
                amount=amount,
                comment=comment,
                status=DonationStatus.pending,
                payment_id=payment["id"],
                confirmation_url=(payment.get("confirmation") or {}).get("confirmation_url"),
            )
        )
        self.db.commit()
        self.db.refresh(donation)
        return donation

    def confirm_payment(self, payment_id: str) -> Donation | None:
        """Вызывается вебхуком ЮKassa. Статус берём отдельным запросом к API, а не из тела
        вебхука — его может подделать кто угодно, у ЮKassa нет подписи в самом JSON."""
        donation = self.repo.get_donation_by_payment_id(payment_id)
        if donation is None or donation.status is not DonationStatus.pending:
            return donation

        gateway = get_gateway()
        if gateway is None:
            return donation
        payment = gateway.get_payment(payment_id)
        remote_status = payment.get("status")

        if remote_status == "succeeded":
            donation.status = DonationStatus.succeeded
            need = self.repo.get(donation.need_id)
            if need is not None:
                self._credit(need, donation.amount)
        elif remote_status in ("canceled", "cancelled"):
            donation.status = DonationStatus.canceled
        else:
            return donation

        self.db.commit()
        self.db.refresh(donation)
        if donation.status is DonationStatus.succeeded and donation.donor_id:
            award_achievement(user_id=donation.donor_id, code=ACHIEVEMENT_DONOR)
        return donation

    def donations_for(self, need_id: str) -> Sequence[Donation]:
        self.get(need_id)
        return self.repo.donations_for(need_id)

    def _credit(self, need: SquadNeed, amount: int) -> None:
        need.collected_amount += amount
        if need.target_amount is not None and need.collected_amount >= need.target_amount:
            need.status = NeedStatus.closed

    # --- helpers ---

    def _leader_of(self, need: SquadNeed) -> str:
        squad = self.squads.get(need.squad_id)
        return squad.leader_id if squad else ""

    @staticmethod
    def _ensure_squad_manager(principal: Principal, leader_id: str) -> None:
        if is_staff(principal) or leader_id == principal.user_id:
            return
        raise PermissionDenied("Управлять потребностями может командир отряда или модератор")
