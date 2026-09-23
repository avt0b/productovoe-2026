from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, new_uuid

# Код — свободная строка, как Notification.kind: новый повод для ачивки
# заводит сервис-источник события, user_service под это не редеплоится.
# Здесь только человекочитаемые заголовки для текста уведомления; для
# неизвестного кода просто покажем сам код.
ACHIEVEMENT_TITLES: dict[str, str] = {
    "first_route_completed": "Первый маршрут пройден",
    "archive_helper": "Помощник архива",
    "trip_volunteer": "Доброволец",
    "donor": "Жертвователь",
}


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "code", name="uq_user_achievement"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
