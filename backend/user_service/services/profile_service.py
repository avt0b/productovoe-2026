from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import PermissionDenied, ProfileNotFound
from core.models import Profile
from core.security import Principal
from repositories.profile_repository import ProfileRepository


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

    def get_many(self, profile_ids: Sequence[str]) -> Sequence[Profile]:
        """Несуществующие id просто пропускаются: профиль создаётся лениво, и
        у автора, ни разу не открывавшего профиль, его может ещё не быть."""
        return self.profiles.get_many(list(dict.fromkeys(profile_ids)))

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
        # Раньше профиль мог подтвердить любой краевед (пиринг) — теперь это
        # делает исключительно администратор при одобрении RoleApplication
        # (см. services/role_application_service.py), пиринговая верификация
        # снята.
        if not actor.is_root:
            raise PermissionDenied("Верифицировать профили может только администратор")
        profile = self.get(profile_id)
        profile.is_verified = is_verified
        self.db.commit()
        self.db.refresh(profile)
        return profile
