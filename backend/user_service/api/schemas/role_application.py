from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from core.models import ApplicationStatus
from core.public_url import PublicUrl


class RoleApplicationCreate(BaseModel):
    requested_role: Literal["searcher", "local_historian"]
    full_name: str = Field(default="", max_length=255)
    contact: str = Field(default="", max_length=300)
    evidence: str = Field(default="", max_length=4000)
    evidence_url: str | None = Field(default=None, max_length=500)


class RoleApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    requested_role: str
    full_name: str
    contact: str
    evidence: str
    evidence_url: PublicUrl | None
    status: ApplicationStatus
    review_note: str
    reviewed_by: str | None
    created_at: datetime


class ReviewRequest(BaseModel):
    note: str = Field(default="", max_length=1000)
