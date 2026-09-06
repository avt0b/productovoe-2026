from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import Profile


class ProfileRepository:
    """Доступ к таблице profiles. Только БД."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, profile_id: str) -> Profile | None:
        return self.db.get(Profile, profile_id)

    def search(
        self, *, role: str | None = None, limit: int = 50, offset: int = 0
    ) -> Sequence[Profile]:
        stmt = select(Profile).order_by(Profile.created_at.desc())
        if role is not None:
            stmt = stmt.where(Profile.role == role)
        return self.db.scalars(stmt.limit(limit).offset(offset)).all()

    def add(self, profile: Profile) -> Profile:
        self.db.add(profile)
        self.db.flush()
        return profile
