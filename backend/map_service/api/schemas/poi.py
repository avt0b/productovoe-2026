from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.common import Lat, Lon
from core.models import POIKind


class POICreate(BaseModel):
    kind: POIKind
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    lat: Lat
    lon: Lon
    event_date: date | None = None
    date_text: str = Field(default="", max_length=120)
    source: str = ""


class POIUpdate(BaseModel):
    kind: POIKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    lat: Lat | None = None
    lon: Lon | None = None
    event_date: date | None = None
    date_text: str | None = Field(default=None, max_length=120)
    source: str | None = None

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class POIOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: POIKind
    title: str
    description: str
    lat: float
    lon: float
    event_date: date | None
    date_text: str
    source: str
    created_by: str
    created_at: datetime


class POINearbyOut(POIOut):
    distance_km: float
