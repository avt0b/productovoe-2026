from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from core.models import Role

# Роли, которые человек выбирает себе сам при регистрации. И поисковиком, и
# краеведом стать самому нельзя — нужна заявка (контакты + доказательства) и
# одобрение администратора (см. RoleApplication в user_service).
SELF_ASSIGNABLE_ROLES = frozenset({Role.family})


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.family

    @field_validator("role")
    @classmethod
    def _role_is_self_assignable(cls, role: Role) -> Role:
        if role not in SELF_ASSIGNABLE_ROLES:
            raise ValueError("Роль поисковика и краеведа выдаётся только по заявке и одобрению администратора")
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
