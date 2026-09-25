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
    # Краевед
    "historian_first_excursion": "Первая экскурсия",
    "historian_led_group": "Проводник",
    "historian_five_stars": "Пять звёзд",
    "historian_route_author": "Автор маршрута",
    "historian_poi_author": "Летописец местности",
    "historian_archive_keeper": "Хранитель архива",
    # Поисковик
    "searcher_squad_founder": "Командир",
    "searcher_trip_organizer": "Организатор выезда",
    "searcher_first_find": "Первая находка",
    "searcher_archive_confirmed": "Подтверждено архивом",
    "searcher_remains_raised": "Боец поднят",
    "searcher_goal_reached": "Сбор закрыт",
}


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "code", name="uq_user_achievement"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
