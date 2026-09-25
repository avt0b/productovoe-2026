import enum
from datetime import date, datetime

from sqlalchemy import (
    Date,
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
from core.models.squad import Squad


class RegistrationStatus(str, enum.Enum):
    registered = "registered"
    cancelled = "cancelled"


class TripStatus(str, enum.Enum):
    planned = "planned"
    cancelled = "cancelled"


class VolunteerTrip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Выезд «Выходные с поисковиком»."""

    __tablename__ = "volunteer_trips"

    squad_id: Mapped[str] = mapped_column(
        ForeignKey("squads.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # Место сбора выезда на карте. Не то же, что штаб отряда (`Squad.lat/lon`):
    # отряд базируется в городе, а собираются у деревни, до которой ехать час.
    # Необязательны: командир объявляет выезд заранее, а место уточняет потом.
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Чек-лист новичка (лопата, щуп, перчатки, регистрация на «Память народа»…).
    checklist: Mapped[str] = mapped_column(Text, default="", nullable=False)

    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_status", native_enum=False, length=16),
        default=TripStatus.planned,
        nullable=False,
        index=True,
    )
    cancel_reason: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    squad: Mapped[Squad] = relationship(back_populates="trips")
    registrations: Mapped[list["TripRegistration"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )


class TripRegistration(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "trip_registrations"
    __table_args__ = (UniqueConstraint("trip_id", "user_id", name="uq_trip_user"),)

    trip_id: Mapped[str] = mapped_column(
        ForeignKey("volunteer_trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status", native_enum=False, length=16),
        default=RegistrationStatus.registered,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    trip: Mapped[VolunteerTrip] = relationship(back_populates="registrations")
