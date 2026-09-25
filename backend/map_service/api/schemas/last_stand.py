from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.common import Lat, Lon
from core.models import LastStandStatus


class LastStandCreate(BaseModel):
    soldier_name: str = Field(default="", max_length=255)
    unit: str = Field(default="", max_length=255)
    lat: Lat
    lon: Lon
    circumstances: str = ""
    death_date: date | None = None
    date_text: str = Field(default="", max_length=120)
    source: str = ""


class LastStandUpdate(BaseModel):
    soldier_name: str | None = Field(default=None, max_length=255)
    unit: str | None = Field(default=None, max_length=255)
    lat: Lat | None = None
    lon: Lon | None = None
    circumstances: str | None = None
    death_date: date | None = None
    date_text: str | None = Field(default=None, max_length=120)
    source: str | None = None

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class LastStandStatusUpdate(BaseModel):
    status: LastStandStatus
    # На основании чего перевели: том Книги Памяти, номер дела, донесение о
    # потерях. Не обязателен, но именно он и делает историю полезной.
    note: str = Field(default="", max_length=1000)


class LastStandStatusChangeOut(BaseModel):
    """Строка истории стадий: кто, когда, с какой на какую и почему."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    point_id: str
    from_status: LastStandStatus | None
    to_status: LastStandStatus
    actor_id: str
    note: str
    created_at: datetime


class LastStandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    soldier_name: str
    unit: str
    lat: float
    lon: float
    circumstances: str
    death_date: date | None
    date_text: str
    source: str
    status: LastStandStatus
    created_by: str
    created_at: datetime


class LastStandNearbyOut(LastStandOut):
    distance_km: float
