from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.models import HeroStatus
from core.public_url import PublicUrl


class FamilyHeroCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    status: HeroStatus = HeroStatus.veteran
    birth_year: int | None = Field(default=None, ge=1850, le=2100)
    death_year: int | None = Field(default=None, ge=1850, le=2100)
    unit: str = Field(default="", max_length=300)
    note: str = Field(default="", max_length=1000)
    photo_url: str | None = Field(default=None, max_length=500)
    archive_entry_id: str | None = Field(default=None, max_length=36)


class FamilyHeroUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: HeroStatus | None = None
    birth_year: int | None = Field(default=None, ge=1850, le=2100)
    death_year: int | None = Field(default=None, ge=1850, le=2100)
    unit: str | None = Field(default=None, max_length=300)
    note: str | None = Field(default=None, max_length=1000)
    photo_url: str | None = Field(default=None, max_length=500)
    archive_entry_id: str | None = Field(default=None, max_length=36)

    # birth_year/death_year/photo_url/archive_entry_id — единственные
    # nullable-поля в модели, туда явный null осмыслен (снять фото, забыть
    # год). Остальные (name/status/unit/note) NOT NULL — явный null для них
    # молча отбрасываем, тот же принцип, что у avatar_url в ProfileUpdate.
    _NULLABLE_FIELDS = {"birth_year", "death_year", "photo_url", "archive_entry_id"}

    def to_update_dict(self) -> dict:
        data = self.model_dump(exclude_unset=True)
        return {k: v for k, v in data.items() if v is not None or k in self._NULLABLE_FIELDS}


class FamilyHeroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    status: HeroStatus
    birth_year: int | None
    death_year: int | None
    unit: str
    note: str
    photo_url: PublicUrl | None
    archive_entry_id: str | None
    created_at: datetime
