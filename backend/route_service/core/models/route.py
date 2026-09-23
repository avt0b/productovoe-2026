import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RouteMode(str, enum.Enum):
    family = "family"  # семейный режим: задания для детей, аудиоспектакли, AR
    general = "general"  # обычная экскурсия


class Route(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "routes"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    mode: Mapped[RouteMode] = mapped_column(
        Enum(RouteMode, name="route_mode", native_enum=False, length=16),
        default=RouteMode.family,
        nullable=False,
    )
    city: Mapped[str] = mapped_column(String(120), default="", nullable=False, index=True)
    distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    waypoints: Mapped[list["Waypoint"]] = relationship(
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="Waypoint.order_index",
    )


class Waypoint(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "waypoints"

    route_id: Mapped[str] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)

    # Ссылка на точку слоя «ВОВ» в map_service (опционально).
    poi_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    story: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Задание для ребёнка: «Найди калибр пушки на иллюстрации».
    kid_task: Mapped[str] = mapped_column(Text, default="", nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ar_hint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Эталонный ответ на kid_task, сверяется на progress/complete-waypoint.
    # Пусто — задание не проверяется (просто факт «дошёл до точки»).
    expected_answer: Mapped[str] = mapped_column(Text, default="", nullable=False)

    route: Mapped[Route] = relationship(back_populates="waypoints")
