from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GuideRatingCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=500)


class GuideRatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    excursion_id: str
    guide_id: str
    rater_id: str
    rating: int
    comment: str
    created_at: datetime


class GuideRatingSummaryOut(BaseModel):
    guide_id: str
    average: float
    count: int
    recent: list[GuideRatingOut]
