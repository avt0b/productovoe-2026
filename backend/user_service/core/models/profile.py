from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"

    # id совпадает с id пользователя из auth_service (sub в JWT).
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    display_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    city: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Кэш роли из JWT — удобно для выборок; источник истины остаётся в auth_service.
    role: Mapped[str] = mapped_column(String(32), default="family", nullable=False)

    # Для роли searcher — привязка к отряду (id из search_hq_service).
    squad_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Верификация краеведа/наставника (ставит модератор).
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Настройки уведомлений «Последний бой»: подписка, радиус и точка отсчёта
    # (без home_lat/home_lon радиус не от чего считать — подписка тогда неактивна).
    subscribed_to_search: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_radius_km: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    home_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
