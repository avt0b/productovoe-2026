from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import UserAchievement


class AchievementRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: str, code: str) -> UserAchievement | None:
        return self.db.scalar(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id, UserAchievement.code == code
            )
        )

    def add(self, achievement: UserAchievement) -> UserAchievement:
        self.db.add(achievement)
        self.db.flush()
        return achievement

    def for_user(self, user_id: str) -> Sequence[UserAchievement]:
        return self.db.scalars(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.earned_at.desc())
        ).all()
