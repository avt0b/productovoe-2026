from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import Donation, DonationStatus, NeedKind, NeedStatus, SquadNeed


class NeedRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, need_id: str) -> SquadNeed | None:
        return self.db.get(SquadNeed, need_id)

    def add(self, need: SquadNeed) -> SquadNeed:
        self.db.add(need)
        self.db.flush()
        return need

    def search(
        self,
        *,
        squad_id: str | None = None,
        kind: NeedKind | None = None,
        status: NeedStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[SquadNeed]:
        stmt = select(SquadNeed)
        if squad_id:
            stmt = stmt.where(SquadNeed.squad_id == squad_id)
        if kind:
            stmt = stmt.where(SquadNeed.kind == kind)
        if status:
            stmt = stmt.where(SquadNeed.status == status)
        return self.db.scalars(
            stmt.order_by(SquadNeed.created_at.desc()).limit(limit).offset(offset)
        ).all()

    def add_donation(self, donation: Donation) -> Donation:
        self.db.add(donation)
        self.db.flush()
        return donation

    def get_donation_by_payment_id(self, payment_id: str) -> Donation | None:
        return self.db.scalar(select(Donation).where(Donation.payment_id == payment_id))

    def donations_for(self, need_id: str, *, limit: int = 200) -> Sequence[Donation]:
        """Публичная и «мои взносы» лента — только реально прошедшие взносы, не pending/canceled."""
        return self.db.scalars(
            select(Donation)
            .where(Donation.need_id == need_id, Donation.status == DonationStatus.succeeded)
            .order_by(Donation.created_at.desc())
            .limit(limit)
        ).all()
