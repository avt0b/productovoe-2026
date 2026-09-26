from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.schemas.excursion import UtcDatetime
from services.profile_client import ProfileBrief
from services.rating_service import GuideCardView, Leaderboard, LeaderboardEntry, ReviewView

# Подписи краеведа, если его профиля нет или user_service не ответил.
FALLBACK_GUIDE_NAME = "Краевед"


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


class GuideReviewOut(GuideRatingOut):
    """Оценка в карточке краеведа — с тем, кто её поставил и за какую экскурсию."""

    rater_name: str
    rater_avatar_url: str | None
    excursion_title: str

    @classmethod
    def from_view(cls, review: ReviewView) -> "GuideReviewOut":
        base = GuideRatingOut.model_validate(review.rating)
        return cls(
            **base.model_dump(),
            rater_name=review.rater_name,
            rater_avatar_url=review.rater_avatar_url,
            excursion_title=review.excursion_title,
        )


class GuideProfileOut(BaseModel):
    display_name: str
    avatar_url: str | None
    city: str
    role: str
    is_verified: bool

    @classmethod
    def maybe(cls, profile: ProfileBrief | None) -> "GuideProfileOut | None":
        if profile is None:
            return None
        return cls(
            display_name=profile.display_name or FALLBACK_GUIDE_NAME,
            avatar_url=profile.avatar_url,
            city=profile.city,
            role=profile.role,
            is_verified=profile.is_verified,
        )


class GuideRatingSummaryOut(BaseModel):
    """Карточка краеведа. Первые четыре поля — прежние, на них завязан веб;
    остальное добавлено для рейтинга и только добавлено."""

    guide_id: str
    average: float
    count: int
    recent: list[GuideReviewOut]
    # null — оценок нет, в рейтинге краевед не участвует.
    score: float | None
    place: int | None
    total_ranked: int
    excursions_led: int
    # Сколько оценок каждого балла; ключи "1"…"5" есть всегда.
    distribution: dict[str, int]
    profile: GuideProfileOut | None

    @classmethod
    def from_view(cls, card: GuideCardView) -> "GuideRatingSummaryOut":
        return cls(
            guide_id=card.guide_id,
            average=card.average,
            count=card.count,
            recent=[GuideReviewOut.from_view(review) for review in card.recent],
            score=card.score,
            place=card.place,
            total_ranked=card.total_ranked,
            excursions_led=card.excursions_led,
            distribution=card.distribution,
            profile=GuideProfileOut.maybe(card.profile),
        )


class GuideRankOut(BaseModel):
    place: int
    guide_id: str
    display_name: str
    avatar_url: str | None
    city: str
    is_verified: bool
    # Обычное среднее — его показывают звёздами.
    average: float
    count: int
    # Байесовское — только для порядка.
    score: float
    # Сколько экскурсий довёл до конца — за всё время, в любом периоде.
    excursions_led: int
    last_rated_at: UtcDatetime | None
    is_me: bool

    @classmethod
    def from_entry(cls, entry: LeaderboardEntry) -> "GuideRankOut":
        profile = entry.profile
        rank = entry.rank
        return cls(
            place=rank.place,
            guide_id=rank.guide_id,
            display_name=profile.display_name if profile and profile.display_name else FALLBACK_GUIDE_NAME,
            avatar_url=profile.avatar_url if profile else None,
            city=profile.city if profile else "",
            is_verified=profile.is_verified if profile else False,
            average=rank.average,
            count=rank.count,
            score=rank.score,
            excursions_led=entry.excursions_led,
            last_rated_at=rank.last_rated_at,
            is_me=entry.is_me,
        )


class GuideLeaderboardOut(BaseModel):
    period: str
    # Среднее всех оценок за период — для сведения, в место не входит.
    global_average: float
    # Сколько «виртуальных» оценок добавляется каждому — «C» в формуле.
    prior_weight: int
    # Какого они балла — «M» в формуле, середина шкалы.
    prior_mean: float
    # Сколько краеведов в рейтинге всего, а не на этой странице.
    total: int
    items: list[GuideRankOut]

    @classmethod
    def from_view(cls, board: Leaderboard) -> "GuideLeaderboardOut":
        return cls(
            period=board.period,
            global_average=board.global_average,
            prior_weight=board.prior_weight,
            prior_mean=board.prior_mean,
            total=board.total,
            items=[GuideRankOut.from_entry(entry) for entry in board.entries],
        )
