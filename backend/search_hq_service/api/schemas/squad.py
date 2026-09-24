from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from core.models import SquadKind

Lat = Annotated[float, Field(ge=-90, le=90)]
Lon = Annotated[float, Field(ge=-180, le=180)]


class SquadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: SquadKind = SquadKind.squad
    region: str = Field(default="", max_length=120)
    description: str = ""
    contact: str = Field(default="", max_length=300)
    lat: Lat | None = None
    lon: Lon | None = None


class SquadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: SquadKind | None = None
    region: str | None = Field(default=None, max_length=120)
    description: str | None = None
    contact: str | None = Field(default=None, max_length=300)
    lat: Lat | None = None
    lon: Lon | None = None

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class SquadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    kind: SquadKind
    region: str
    description: str
    contact: str
    leader_id: str
    lat: float | None
    lon: float | None
    created_at: datetime
