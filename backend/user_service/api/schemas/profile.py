from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.achievement import AchievementOut
from api.schemas.family_hero import FamilyHeroOut
from core.public_url import PublicUrl


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    city: str
    bio: str
    avatar_url: PublicUrl | None
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
    # Та же история, что и с achievements выше — заполняются только там, где
    # запрошены явно (GET /profiles/me, GET /profiles/{id}), иначе дефолт 0.
    routes_completed: int = 0
    excursions_completed: int = 0
    finds_count: int = 0
    # Семейное древо — та же логика: заполняется явно в GET /profiles/me и
    # GET /profiles/{id}, видно и на своём, и на чужом профиле.
    heroes: list[FamilyHeroOut] = []
    created_at: datetime


class ProfileBriefOut(BaseModel):
    """Публичная карточка автора — для подписи в лентах (GET /profiles/batch).

    Намеренно без home_lat/home_lon, радиуса оповещений и подписок: батч
    отдаётся без токена, по любым id."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    avatar_url: PublicUrl | None
    role: str
    is_verified: bool


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
