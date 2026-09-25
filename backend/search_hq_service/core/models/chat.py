import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin
from core.timeutil import utcnow


class ChatSubjectType(str, enum.Enum):
    trip = "trip"
    excursion = "excursion"


class ChatMessage(UUIDPrimaryKeyMixin, Base):
    """Сообщение в чате сбора (выезд «Выходные с поисковиком» или экскурсия).

    Без FK на trip/excursion: одна таблица обслуживает оба типа сбора, а
    заводить по внешнему ключу на каждый — усложнение ради одной таблицы.
    Поэтому переписку удалённого выезда (и выездов распущенного отряда)
    сервис убирает сам — `ChatRepository.delete_for`.
    """

    __tablename__ = "chat_messages"
    __table_args__ = (Index("ix_chat_messages_subject", "subject_type", "subject_id"),)

    subject_type: Mapped[ChatSubjectType] = mapped_column(
        Enum(ChatSubjectType, name="chat_subject_type", native_enum=False, length=16),
        nullable=False,
    )
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Время ставит приложение: у SQLite `now()` — с точностью до секунды, и
    # сообщения, отправленные подряд, получали бы одно время и путались в порядке.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), index=True
    )
