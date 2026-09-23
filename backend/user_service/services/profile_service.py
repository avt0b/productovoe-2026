from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import PermissionDenied, ProfileNotFound
from core.models import Profile
from core.security import Principal
from repositories.profile_repository import ProfileRepository

_VERIFIER_ROLES = {"moderator", "local_historian", "mentor"}


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.profiles = ProfileRepository(db)

    def get_or_create_own(self, principal: Principal) -> Profile:
        """Профиль создаётся лениво при первом обращении, id = id пользователя."""
        profile = self.profiles.get(principal.user_id)
        if profile is None:
            profile = self.profiles.add(Profile(id=principal.user_id, role=principal.role))
            self.db.commit()
            self.db.refresh(profile)
        elif profile.role != principal.role:
            profile.role = principal.role  # держим кэш роли в актуальном состоянии
            self.db.commit()
        return profile

    def get(self, profile_id: str) -> Profile:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise ProfileNotFound
        return profile

    def search(
        self, *, role: str | None = None, limit: int = 50, offset: int = 0
    ) -> Sequence[Profile]:
        return self.profiles.search(role=role, limit=limit, offset=offset)

    def update_own(self, principal: Principal, data: dict) -> Profile:
        profile = self.get_or_create_own(principal)
        for field, value in data.items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def set_verified(self, actor: Principal, profile_id: str, is_verified: bool) -> Profile:
        if not (actor.is_root or actor.role in _VERIFIER_ROLES):
            raise PermissionDenied("Верифицировать профили может модератор/краевед")
        profile = self.get(profile_id)
        profile.is_verified = is_verified
        self.db.commit()
        self.db.refresh(profile)
        return profile
