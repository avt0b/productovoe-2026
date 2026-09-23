from sqlalchemy.orm import Session

from core.models import ProfileStat
from repositories.profile_stat_repository import ProfileStatRepository


class StatsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProfileStatRepository(db)

    def increment(self, *, user_id: str, metric: str, by: int = 1) -> ProfileStat:
        stat = self.repo.get(user_id, metric)
        if stat is None:
            stat = self.repo.add(ProfileStat(user_id=user_id, metric=metric, value=0))
        stat.value += by
        self.db.commit()
        self.db.refresh(stat)
        return stat

    def for_user(self, user_id: str) -> dict[str, int]:
        return {row.metric: row.value for row in self.repo.for_user(user_id)}
