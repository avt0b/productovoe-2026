import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, UUIDPrimaryKeyMixin


class ChatSubjectType(str, enum.Enum):
    trip = "trip"
    excursion = "excursion"


class ChatMessage(UUIDPrimaryKeyMixin, Base):
    """Сообщение в чате сбора (выезд «Выходные с поисковиком» или экскурсия).

    Без FK на trip/excursion: одна таблица обслуживает оба типа сбора, а
    заводить по внешнему ключу на каждый — усложнение ради одной таблицы.
    Удаления сборов сейчас в API нет, так что осиротевшие сообщения не
    возникают на практике.
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
