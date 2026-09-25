import enum
from datetime import date

from datetime import datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


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


class LastStandStatusChange(UUIDPrimaryKeyMixin, Base):
    """Кто и почему перевёл место на другую стадию.

    Сама точка помнит только последнее состояние, а «подтверждено архивом» —
    это утверждение о факте: народный архив держится на том, что видно, кто за
    ним стоит. Записи только добавляются: строка истории не правится и не
    удаляется, иначе она ничего не стоит."""

    __tablename__ = "last_stand_status_changes"

    point_id: Mapped[str] = mapped_column(
        ForeignKey("last_stand_points.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Стадия до перевода. None — точку завели сразу с этой стадией.
    from_status: Mapped[LastStandStatus | None] = mapped_column(
        Enum(LastStandStatus, name="last_stand_status", native_enum=False, length=32), nullable=True
    )
    to_status: Mapped[LastStandStatus] = mapped_column(
        Enum(LastStandStatus, name="last_stand_status", native_enum=False, length=32),
        nullable=False,
    )
    actor_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # На основании чего: том Книги Памяти, номер дела, донесение о потерях.
    note: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    # Время ставит Python, а не СУБД: CURRENT_TIMESTAMP в SQLite округляет до
    # секунды, и две записи одной сессии ложились бы в один момент — порядок
    # истории становился случайным.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
