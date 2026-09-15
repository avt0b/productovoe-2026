from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.models import NeedKind, NeedStatus


class NeedCreate(BaseModel):
    kind: NeedKind
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    target_amount: int | None = Field(default=None, ge=1)


class NeedUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    target_amount: int | None = Field(default=None, ge=1)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class NeedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    squad_id: str
    kind: NeedKind
    title: str
    description: str
    target_amount: int | None
    collected_amount: int
    status: NeedStatus
    created_at: datetime


class DonationCreate(BaseModel):
    amount: int = Field(ge=1, le=10_000_000)
    comment: str = Field(default="", max_length=500)


class DonationOut(BaseModel):
    """Взнос — ответ самому жертвователю, поэтому с его donor_id."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    need_id: str
    donor_id: str | None
    amount: int
    comment: str
    created_at: datetime


class DonationPublicOut(BaseModel):
    """Взнос в публичной ленте сбора: без donor_id — кто сколько дал, наружу не показываем."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    need_id: str
    amount: int
    comment: str
    created_at: datetime
