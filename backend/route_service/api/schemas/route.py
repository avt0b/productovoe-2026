from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from core.models import RouteMode

Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]


class RouteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    mode: RouteMode = RouteMode.family
    city: str = Field(default="", max_length=120)
    distance_km: float = Field(default=0.0, ge=0, le=100)
    cover_url: str | None = Field(default=None, max_length=500)


class RouteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    mode: RouteMode | None = None
    city: str | None = Field(default=None, max_length=120)
    distance_km: float | None = Field(default=None, ge=0, le=100)
    cover_url: str | None = Field(default=None, max_length=500)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class WaypointCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    lat: Lat
    lon: Lon
    poi_id: str | None = Field(default=None, max_length=36)
    story: str = ""
    kid_task: str = ""
    audio_url: str | None = Field(default=None, max_length=500)
    ar_hint: str = ""
    order_index: int | None = Field(default=None, ge=0)


class WaypointUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    lat: Lat | None = None
    lon: Lon | None = None
    poi_id: str | None = Field(default=None, max_length=36)
    story: str | None = None
    kid_task: str | None = None
    audio_url: str | None = Field(default=None, max_length=500)
    ar_hint: str | None = None
    order_index: int | None = Field(default=None, ge=0)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class WaypointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_id: str
    order_index: int
    title: str
    lat: float
    lon: float
    poi_id: str | None
    story: str
    kid_task: str
    audio_url: str | None
    ar_hint: str


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    mode: RouteMode
    city: str
    distance_km: float
    cover_url: str | None
    created_by: str
    is_published: bool
    created_at: datetime


class RouteDetailOut(RouteOut):
    waypoints: list[WaypointOut] = []


class ReorderRequest(BaseModel):
    ordered_ids: list[str] = Field(min_length=1)


class PublishRequest(BaseModel):
    is_published: bool = True


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    user_id: str
    completed_waypoint_ids: list[str]
    current_index: int
    started_at: datetime
    completed_at: datetime | None


class CompleteWaypointRequest(BaseModel):
    waypoint_id: str
