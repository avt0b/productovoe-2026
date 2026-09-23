from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    earned_at: datetime


class AwardRequest(BaseModel):
    """Тело вызова из сервиса-источника события (route_service на завершении
    маршрута, archive_service на верификации, search_hq_service на выезде/
    донате). Идемпотентно на стороне user_service."""

    user_id: str = Field(min_length=1, max_length=36)
    code: str = Field(min_length=1, max_length=64)


class AwardOut(BaseModel):
    code: str
    awarded: bool
