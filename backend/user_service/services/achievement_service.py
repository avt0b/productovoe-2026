from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.models import ACHIEVEMENT_TITLES, Notification, UserAchievement
from repositories.achievement_repository import AchievementRepository
from repositories.notification_repository import NotificationRepository


class AchievementService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AchievementRepository(db)
        self.notifications = NotificationRepository(db)

    def award(self, *, user_id: str, code: str) -> tuple[UserAchievement, bool]:
        """Идемпотентно: повторный award тем же (user_id, code) не дублирует
        запись и не шлёт уведомление ещё раз — сервисы-источники событий
        (route_service на завершении маршрута и т.п.) могут звать это на
        каждое подходящее действие, не выясняя заранее, было ли оно первым."""
        existing = self.repo.get(user_id, code)
        if existing is not None:
            return existing, False

        achievement = self.repo.add(UserAchievement(user_id=user_id, code=code))
        title = ACHIEVEMENT_TITLES.get(code, code)
        self.notifications.add(
            Notification(
                user_id=user_id,
                kind="achievement",
                title="Новое достижение!",
                body=title,
                payload={"code": code},
            )
        )
        self.db.commit()
        self.db.refresh(achievement)
        return achievement, True

    def list_for(self, user_id: str) -> Sequence[UserAchievement]:
        return self.repo.for_user(user_id)
