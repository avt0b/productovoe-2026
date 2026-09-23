from collections.abc import Sequence

from sqlalchemy import select
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
    ) -> Sequence[ChatMessage]:
        return self.db.scalars(
            select(ChatMessage)
            .where(ChatMessage.subject_type == subject_type, ChatMessage.subject_id == subject_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        ).all()
