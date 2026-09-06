from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SquadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    region: str = Field(default="", max_length=120)
    description: str = ""
    contact: str = Field(default="", max_length=300)


class SquadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    region: str | None = Field(default=None, max_length=120)
    description: str | None = None
    contact: str | None = Field(default=None, max_length=300)

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class SquadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    region: str
    description: str
    contact: str
    leader_id: str
    created_at: datetime
