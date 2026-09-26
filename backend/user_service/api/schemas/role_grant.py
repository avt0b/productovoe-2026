import uuid

from pydantic import BaseModel, Field


class RoleGrantRedeem(BaseModel):
    # Ключ с метки: 32 байта в base64url — 43 символа.
    key: str = Field(min_length=16, max_length=128)
    # Кому выдать. uuid, а не ник: ники не уникальны.
    user_id: uuid.UUID
    nickname: str = Field(default="", max_length=120)


class RoleGrantOut(BaseModel):
    user_id: str
    role: str
    previous_role: str
    # Роль уже была — ничего не поменялось, но приложение всё равно празднует.
    already: bool
