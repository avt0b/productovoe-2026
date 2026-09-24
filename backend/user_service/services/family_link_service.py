import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound
from core.models import FamilyLink, FamilyLinkInvite
from core.security import Principal
from core.timeutil import as_utc, utcnow
from repositories.family_link_repository import FamilyLinkRepository
from repositories.profile_repository import ProfileRepository

# Без похожих друг на друга символов (0/O, 1/I/l) — код читают и вводят руками.
_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_CODE_LENGTH = 8
_INVITE_TTL_DAYS = 7


class FamilyLinkService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FamilyLinkRepository(db)
        self.profiles = ProfileRepository(db)

    def create_invite(self, principal: Principal) -> FamilyLinkInvite:
        code = self._generate_code()
        invite = self.repo.add_invite(
            FamilyLinkInvite(
                inviter_id=principal.user_id,
                code=code,
                expires_at=utcnow() + timedelta(days=_INVITE_TTL_DAYS),
            )
        )
        self.db.commit()
        self.db.refresh(invite)
        return invite

    def redeem_invite(self, principal: Principal, code: str) -> FamilyLink:
        invite = self.repo.get_invite_by_code(code.strip().upper())
        if invite is None:
            raise NotFound("Код не найден")
        if invite.used_by is not None:
            raise Conflict("Код уже использован")
        if as_utc(invite.expires_at) < utcnow():
            raise Conflict("Код просрочен")
        if invite.inviter_id == principal.user_id:
            raise Conflict("Нельзя использовать собственный код")

        invite.used_by = principal.user_id
        invite.used_at = utcnow()

        if not self.repo.exists(invite.inviter_id, principal.user_id):
            self.repo.add_link(FamilyLink(owner_id=invite.inviter_id, member_id=principal.user_id))
        link = self.repo.get_link(principal.user_id, invite.inviter_id)
        if link is None:
            link = self.repo.add_link(
                FamilyLink(owner_id=principal.user_id, member_id=invite.inviter_id)
            )
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_mine(self, principal: Principal) -> list[dict]:
        links = self.repo.for_owner(principal.user_id)
        out = []
        for link in links:
            profile = self.profiles.get(link.member_id)
            out.append(
                {
                    "member_id": link.member_id,
                    "display_name": profile.display_name if profile else "",
                    "city": profile.city if profile else "",
                    "avatar_url": profile.avatar_url if profile else None,
                    "home_lat": profile.home_lat if profile else None,
                    "home_lon": profile.home_lon if profile else None,
                    "linked_at": link.created_at,
                }
            )
        return out

    def remove(self, principal: Principal, member_id: str) -> None:
        if not self.repo.exists(principal.user_id, member_id):
            raise NotFound("Такой связи нет")
        self.repo.remove_pair(principal.user_id, member_id)
        self.db.commit()

    @staticmethod
    def _generate_code() -> str:
        return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
