from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from core.models import Role

# Роли, которые человек выбирает себе сам при регистрации. Модератор подтверждает
# записи архива и закрывает сборы — эту роль выдаёт только администратор.
SELF_ASSIGNABLE_ROLES = frozenset({Role.family, Role.searcher, Role.local_historian, Role.mentor})


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.family

    @field_validator("role")
    @classmethod
    def _role_is_self_assignable(cls, role: Role) -> Role:
        if role not in SELF_ASSIGNABLE_ROLES:
            raise ValueError("Роль модератора выдаётся только из админки")
        return role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: Role
    is_root: bool
    is_active: bool
    created_at: datetime


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class RoleUpdate(BaseModel):
    role: Role
