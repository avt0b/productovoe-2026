import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from core.models.trip import RegistrationStatus


class ExcursionStatus(str, enum.Enum):
    """Жизненный цикл экскурсии краеведа."""

    scheduled = "scheduled"  # заявка опубликована, идёт запись
    gathering = "gathering"  # краевед на месте, группа отмечается бампом
    finished = "finished"  # сбор закрыт
    cancelled = "cancelled"  # краевед отменил экскурсию


class Excursion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Экскурсия краеведа или наставника в точке на карте."""

    __tablename__ = "excursions"

    # id краеведа (пользователь из auth_service).
    guide_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Место сбора группы: бамп засчитывается только рядом с этой точкой.
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    place_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # То же место на слое «ВОВ» в map_service, если экскурсия у памятника.
    poi_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=20, nullable=False)

    status: Mapped[ExcursionStatus] = mapped_column(
        Enum(ExcursionStatus, name="excursion_status", native_enum=False, length=16),
        default=ExcursionStatus.scheduled,
        nullable=False,
        index=True,
    )
    gathering_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    gathering_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    participants: Mapped[list["ExcursionParticipant"]] = relationship(
        back_populates="excursion", cascade="all, delete-orphan"
    )


class ExcursionParticipant(UUIDPrimaryKeyMixin, Base):
    """Запись человека на экскурсию и отметка, что он пришёл."""

    __tablename__ = "excursion_participants"
    __table_args__ = (UniqueConstraint("excursion_id", "user_id", name="uq_excursion_user"),)

    excursion_id: Mapped[str] = mapped_column(
        ForeignKey("excursions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status", native_enum=False, length=16),
        default=RegistrationStatus.registered,
        nullable=False,
    )
    # Момент, когда бамп с краеведом совпал: человек реально пришёл на место.
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    excursion: Mapped[Excursion] = relationship(back_populates="participants")
