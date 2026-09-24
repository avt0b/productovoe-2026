from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.models import ChatMessage, ChatSubjectType


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        self.db.flush()
        return message

    def list_for(
        self,
        subject_type: ChatSubjectType,
        subject_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        since: datetime | None = None,
    ) -> list[ChatMessage]:
        """Последние `limit` сообщений по порядку. `offset` — сколько самых новых
        пропустить (листать историю назад). `since` — только написанные не
        раньше: так клиент догружает пропущенное после обрыва потока, а
        повторы отсекает по id."""
        where = [ChatMessage.subject_type == subject_type, ChatMessage.subject_id == subject_id]
        if since is not None:
            where.append(ChatMessage.created_at >= since)
        newest_first = self.db.scalars(
            select(ChatMessage)
            .where(*where)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return list(reversed(newest_first))

    def delete_for(self, subject_type: ChatSubjectType, subject_ids: Sequence[str]) -> None:
        if subject_ids:
            self.db.execute(
                delete(ChatMessage).where(
                    ChatMessage.subject_type == subject_type,
                    ChatMessage.subject_id.in_(subject_ids),
                )
            )
