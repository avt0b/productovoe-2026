from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from core.models import DevicePlatform


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    title: str
    body: str
    payload: dict | None
    read_at: datetime | None
    created_at: datetime


class DeviceRegister(BaseModel):
    platform: DevicePlatform
    token: str = Field(min_length=1, max_length=500)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: DevicePlatform
    token: str
    created_at: datetime


Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]


class BroadcastNearbyRequest(BaseModel):
    """Тело вызова из map_service при создании точки «Последнего боя»."""

    lat: Lat
    lon: Lon
    kind: str = Field(default="last_stand_nearby", max_length=64)
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="", max_length=2000)
    payload: dict | None = None


class BroadcastNearbyOut(BaseModel):
    notified: int
