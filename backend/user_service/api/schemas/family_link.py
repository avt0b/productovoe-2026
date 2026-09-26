from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.public_url import PublicUrl


class FamilyLinkInviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    expires_at: datetime


class RedeemRequest(BaseModel):
    code: str = Field(min_length=1, max_length=8)


class FamilyMemberOut(BaseModel):
    member_id: str
    display_name: str
    city: str
    avatar_url: PublicUrl | None
    home_lat: float | None
    home_lon: float | None
    linked_at: datetime


class FamilyIdsOut(BaseModel):
    """Семья человека для других сервисов: только id, без имён и координат."""

    user_id: str
    member_ids: list[str]
