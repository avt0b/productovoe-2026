from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    city: str
    bio: str
    avatar_url: str | None
    role: str
    squad_id: str | None
    is_verified: bool
    subscribed_to_search: bool
    alert_radius_km: int
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Все поля опциональны — обновляется только присланное."""

    display_name: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=4000)
    avatar_url: str | None = Field(default=None, max_length=500)
    squad_id: str | None = Field(default=None, max_length=36)
    subscribed_to_search: bool | None = None
    alert_radius_km: int | None = Field(default=None, ge=1, le=200)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True, exclude_none=True)


class VerifyRequest(BaseModel):
    is_verified: bool = True
