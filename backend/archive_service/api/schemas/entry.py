from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.models import EntryKind, EntryStatus

Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]


class EntryCreate(BaseModel):
    kind: EntryKind
    title: str = Field(min_length=1, max_length=255)
    body: str = ""
    lat: Lat | None = None
    lon: Lon | None = None
    event_date: date | None = None
    date_text: str = Field(default="", max_length=120)
    media_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _coords_together(self):
        if (self.lat is None) != (self.lon is None):
            raise ValueError("lat и lon указываются вместе")
        return self


class EntryUpdate(BaseModel):
    kind: EntryKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = None
    lat: Lat | None = None
    lon: Lon | None = None
    event_date: date | None = None
    date_text: str | None = Field(default=None, max_length=120)
    media_url: str | None = Field(default=None, max_length=500)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class ReviewRequest(BaseModel):
    note: str = Field(default="", max_length=1000)


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: EntryKind
    title: str
    body: str
    lat: float | None
    lon: float | None
    event_date: date | None
    date_text: str
    media_url: str | None
    submitted_by: str
    status: EntryStatus
    verified_by: str | None
    reviewed_at: datetime | None
    review_note: str
    created_at: datetime


class EntryPublicOut(BaseModel):
    """Как EntryOut, но без служебной заметки модератора (review_note) —
    она не предназначена для посторонних глаз."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: EntryKind
    title: str
    body: str
    lat: float | None
    lon: float | None
    event_date: date | None
    date_text: str
    media_url: str | None
    submitted_by: str
    status: EntryStatus
    verified_by: str | None
    reviewed_at: datetime | None
    created_at: datetime
