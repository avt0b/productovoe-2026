import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EntryKind(str, enum.Enum):
    """Тип записи «народного архива»."""

    event = "event"  # локальное событие / бой, не попавший в федеральные базы
    soldier_card = "soldier_card"  # карточка бойца
    memory = "memory"  # воспоминание очевидца
    photo_story = "photo_story"  # фото + история


class EntryStatus(str, enum.Enum):
    pending = "pending"  # предложено пользователем, ждёт проверки
    verified = "verified"  # подтверждено краеведом / поисковым отрядом
    rejected = "rejected"  # отклонено


class ArchiveEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "archive_entries"

    kind: Mapped[EntryKind] = mapped_column(
        Enum(EntryKind, name="entry_kind", native_enum=False, length=32), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Необязательная привязка к точке на карте / маршруте.
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_text: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    # Фото к записи. Имя историческое — поле было единственным вложением.
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Аудиовоспоминание — может быть у записи вместе с фото.
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    submitted_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    status: Mapped[EntryStatus] = mapped_column(
        Enum(EntryStatus, name="entry_status", native_enum=False, length=16),
        default=EntryStatus.pending,
        nullable=False,
        index=True,
    )
    verified_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str] = mapped_column(String(1000), default="", nullable=False)

    __table_args__ = (Index("ix_entry_bbox", "lat", "lon"),)
