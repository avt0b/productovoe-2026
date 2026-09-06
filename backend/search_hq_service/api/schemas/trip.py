from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from core.models import RegistrationStatus


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    location: str = Field(default="", max_length=255)
    starts_on: date
    capacity: int = Field(default=10, ge=1, le=1000)
    description: str = ""
    checklist: str = ""


class TripUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    starts_on: date | None = None
    capacity: int | None = Field(default=None, ge=1, le=1000)
    description: str | None = None
    checklist: str | None = None

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class TripOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    squad_id: str
    title: str
    location: str
    starts_on: date
    capacity: int
    description: str
    checklist: str
    created_at: datetime


class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    user_id: str
    status: RegistrationStatus
    created_at: datetime
