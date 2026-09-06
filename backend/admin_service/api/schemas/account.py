from pydantic import BaseModel, EmailStr, Field

from core.models import AdminRole


class AdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(default="", max_length=200)
    role: AdminRole = AdminRole.viewer


class AdminUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    role: AdminRole | None = None

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True, exclude_none=True)


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


class ActiveUpdate(BaseModel):
    is_active: bool
