from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import ProfileStat


class ProfileStatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: str, metric: str) -> ProfileStat | None:
        return self.db.scalar(
            select(ProfileStat).where(ProfileStat.user_id == user_id, ProfileStat.metric == metric)
        )

    def add(self, stat: ProfileStat) -> ProfileStat:
        self.db.add(stat)
        self.db.flush()
        return stat

    def for_user(self, user_id: str) -> Sequence[ProfileStat]:
        return self.db.scalars(select(ProfileStat).where(ProfileStat.user_id == user_id)).all()
