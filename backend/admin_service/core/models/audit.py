import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin


class AuditOutcome(str, enum.Enum):
    success = "success"
    denied = "denied"  # не хватило прав
    failed = "failed"  # сервис отказал / упал


class AuditLogEntry(UUIDPrimaryKeyMixin, Base):
    """Неизменяемый журнал действий администраторов.

    Для мемориального проекта это не «на будущее», а требование: должно быть
    видно, кто и на каком основании поправил данные о погибшем. Записи только
    добавляются — API на изменение и удаление здесь намеренно нет.
    """

    __tablename__ = "admin_audit_log"

    actor_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    actor_email: Mapped[str] = mapped_column(String(320), default="", nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), default="", nullable=False)

    # Машиночитаемое имя действия: "user.role.set", "entry.verify", "clip.retry"…
    action: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    # На каком сервисе и над чем совершено.
    target_service: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    # Человекочитаемое описание для колонки «Объект» в журнале.
    target_label: Mapped[str] = mapped_column(String(400), default="", nullable=False)

    outcome: Mapped[AuditOutcome] = mapped_column(
        Enum(AuditOutcome, name="audit_outcome", native_enum=False, length=16),
        default=AuditOutcome.success,
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    # Что именно поменялось: {"before": ..., "after": ..., "reason": ...}
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    ip: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(String(400), default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (Index("ix_audit_actor_created", "actor_id", "created_at"),)
