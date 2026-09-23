from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.achievement import AchievementOut


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    city: str
    bio: str
    avatar_url: str | None
    role: str
    squad_id: str | None
    is_verified: bool
    subscribed_to_search: bool
    alert_radius_km: int
    home_lat: float | None
    home_lon: float | None
    # Значки видны на любом профиле, включая чужой (GET /profiles/{id} и так
    # уже отдаёт профиль целиком кому угодно — см. README, «не проверяет
    # владение»). Дефолт [] — на месте, где achievements не подгружали явно
    # (PUT/verify/список), model_validate(profile) просто оставит пусто.
    achievements: list[AchievementOut] = []
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Все поля опциональны — обновляется только присланное."""

    display_name: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=4000)
    avatar_url: str | None = Field(default=None, max_length=500)
    squad_id: str | None = Field(default=None, max_length=36)
    subscribed_to_search: bool | None = None
    alert_radius_km: int | None = Field(default=None, ge=1, le=200)
    home_lat: float | None = Field(default=None, ge=-90, le=90)
    home_lon: float | None = Field(default=None, ge=-180, le=180)

    def to_update_dict(self) -> dict:
        # avatar_url — единственное поле, где null осмыслен (снять аватарку):
        # остальные строковые поля в модели NOT NULL, слать под них null незачем.
        data = self.model_dump(exclude_unset=True)
        return {k: v for k, v in data.items() if v is not None or k == "avatar_url"}


class VerifyRequest(BaseModel):
    is_verified: bool = True
