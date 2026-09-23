from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    author_id: str
    body: str
    created_at: datetime
