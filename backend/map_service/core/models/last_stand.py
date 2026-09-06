import enum
from datetime import date

from sqlalchemy import Date, Enum, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LastStandStatus(str, enum.Enum):
    """Статус точки на карте «Последний бой» (модуль 8 ТЗ)."""

    discovered = "discovered"  # обнаружено место, требуется проверка
    archive_confirmed = "archive_confirmed"  # подтверждено архивом
    remains_raised = "remains_raised"  # останки подняты, захоронение состоялось


class LastStandPoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Место гибели красноармейца — даже если останки не подняты / боец пропал без вести."""

    __tablename__ = "last_stand_points"

    # Может быть неизвестен.
    soldier_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    unit: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)

    circumstances: Mapped[str] = mapped_column(Text, default="", nullable=False)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_text: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    # Книга Памяти (том), «Память народа», рассказы местных жителей и т.п.
    source: Mapped[str] = mapped_column(Text, default="", nullable=False)

    status: Mapped[LastStandStatus] = mapped_column(
        Enum(LastStandStatus, name="last_stand_status", native_enum=False, length=32),
        default=LastStandStatus.discovered,
        nullable=False,
        index=True,
    )

    created_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    __table_args__ = (Index("ix_last_stand_bbox", "lat", "lon"),)
