import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ClipStatus(str, enum.Enum):
    queued = "queued"  # заявка принята, ждёт воркер
    processing = "processing"  # идёт генерация (NeRF / face reenactment / lip-sync)
    ready = "ready"  # видео готово
    failed = "failed"  # ошибка генерации


class VoiceStyle(str, enum.Enum):
    era_male = "era_male"  # мужской голос, близкий к эпохе
    era_female = "era_female"
    neutral = "neutral"


class MemorialClip(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """«Живое фото» — оживлённая фотография бойца (15–30 сек)."""

    __tablename__ = "memorial_clips"

    soldier_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    source_photo_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Текст от первого лица, который «произносит» боец.
    narration_text: Mapped[str] = mapped_column(
        Text,
        default="Я сделал это, чтобы ты жил и видел голубое небо. Помни меня.",
        nullable=False,
    )
    voice_style: Mapped[VoiceStyle] = mapped_column(
        Enum(VoiceStyle, name="voice_style", native_enum=False, length=16),
        default=VoiceStyle.era_male,
        nullable=False,
    )

    submitted_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Этическая оговорка ТЗ: только мемориальное использование, без коммерции.
    consent_memorial_use: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    status: Mapped[ClipStatus] = mapped_column(
        Enum(ClipStatus, name="clip_status", native_enum=False, length=16),
        default=ClipStatus.queued,
        nullable=False,
        index=True,
    )
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    rendered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Необязательная связь с карточкой бойца в archive_service.
    archive_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    shares: Mapped[list["ClipShare"]] = relationship(
        back_populates="clip", cascade="all, delete-orphan"
    )


class ClipShare(UUIDPrimaryKeyMixin, Base):
    """Кнопка «Отправить родным» — фиксация факта отправки потомкам."""

    __tablename__ = "clip_shares"

    clip_id: Mapped[str] = mapped_column(
        ForeignKey("memorial_clips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    shared_by: Mapped[str] = mapped_column(String(36), nullable=False)
    recipient: Mapped[str] = mapped_column(String(300), nullable=False)
    note: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clip: Mapped[MemorialClip] = relationship(back_populates="shares")
