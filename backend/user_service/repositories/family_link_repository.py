from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.models import FamilyLink, FamilyLinkInvite


class FamilyLinkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- инвайты ---

    def add_invite(self, invite: FamilyLinkInvite) -> FamilyLinkInvite:
        self.db.add(invite)
        self.db.flush()
        return invite

    def get_invite_by_code(self, code: str) -> FamilyLinkInvite | None:
        return self.db.scalars(
            select(FamilyLinkInvite).where(FamilyLinkInvite.code == code)
        ).first()

    def code_taken(self, code: str) -> bool:
        return self.get_invite_by_code(code) is not None

    # --- связи ---

    def add_link(self, link: FamilyLink) -> FamilyLink:
        self.db.add(link)
        self.db.flush()
        return link

    def for_owner(self, owner_id: str) -> Sequence[FamilyLink]:
        return self.db.scalars(
            select(FamilyLink)
            .where(FamilyLink.owner_id == owner_id)
            .order_by(FamilyLink.created_at.asc())
        ).all()

    def get_link(self, owner_id: str, member_id: str) -> FamilyLink | None:
        return self.db.scalars(
            select(FamilyLink).where(
                FamilyLink.owner_id == owner_id, FamilyLink.member_id == member_id
            )
        ).first()

    def exists(self, owner_id: str, member_id: str) -> bool:
        return self.get_link(owner_id, member_id) is not None

    def remove_pair(self, owner_id: str, member_id: str) -> None:
        self.db.execute(
            delete(FamilyLink).where(
                (FamilyLink.owner_id == owner_id) & (FamilyLink.member_id == member_id)
                | (FamilyLink.owner_id == member_id) & (FamilyLink.member_id == owner_id)
            )
        )
