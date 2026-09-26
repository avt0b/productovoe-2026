from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import ExcursionStatus, GuideRating
from core.security import Principal
from core.timeutil import as_utc, utcnow
from repositories.excursion_repository import ExcursionRepository
from repositories.rating_repository import GuideTotals, RatingRepository
from services import achievement_client, profile_client
from services.profile_client import ProfileBrief

RatingPeriod = Literal["all", "month"]

# «За месяц» — скользящие 30 дней от сейчас, а не календарный месяц: первого
# числа рейтинг иначе обнулялся бы у всех разом.
PERIOD_WINDOW: dict[str, timedelta | None] = {"all": None, "month": timedelta(days=30)}

# Подпись оценщика, если его профиля нет.
FALLBACK_RATER_NAME = "Участник экскурсии"


@dataclass(frozen=True)
class GuideRank:
    place: int
    guide_id: str
    # Обычное среднее — его показывают звёздами.
    average: float
    count: int
    # Байесовское — только для порядка, людям не показываем.
    score: float
    last_rated_at: datetime | None


@dataclass(frozen=True)
class Ranking:
    # Среднее всех оценок всех краеведов за период — для сведения, в место не входит.
    global_average: float
    # Все краеведы с оценками за период, уже по местам.
    ranks: list[GuideRank]


@dataclass(frozen=True)
class LeaderboardEntry:
    rank: GuideRank
    profile: ProfileBrief | None
    excursions_led: int
    is_me: bool


@dataclass(frozen=True)
class Leaderboard:
    period: str
    global_average: float
    prior_weight: int
    prior_mean: float
    total: int
    entries: list[LeaderboardEntry]


@dataclass(frozen=True)
class ReviewView:
    rating: GuideRating
    rater_name: str
    rater_avatar_url: str | None
    excursion_title: str


@dataclass(frozen=True)
class GuideCardView:
    guide_id: str
    average: float
    count: int
    recent: list[ReviewView]
    # None — оценок нет, в рейтинге краевед не участвует.
    score: float | None
    place: int | None
    total_ranked: int
    excursions_led: int
    distribution: dict[str, int]
    profile: ProfileBrief | None


class RatingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RatingRepository(db)
        self.excursions = ExcursionRepository(db)

    def rate(
        self, principal: Principal, excursion_id: str, *, rating: int, comment: str
    ) -> GuideRating:
        excursion = self.excursions.get(excursion_id)
        if excursion is None:
            raise NotFound("Экскурсия не найдена")
        if excursion.guide_id == principal.user_id:
            raise Conflict("Краевед не оценивает свою экскурсию")
        if excursion.status is not ExcursionStatus.finished:
            raise Conflict("Оценить можно только завершённую экскурсию")

        participant = self.excursions.get_participant(excursion_id, principal.user_id)
        if participant is None or participant.checked_in_at is None:
            raise PermissionDenied("Оценивать может только участник, который реально пришёл")

        existing = self.repo.get_by_rater(excursion_id, principal.user_id)
        if existing is not None:
            existing.rating = rating
            existing.comment = comment
            self.db.commit()
            self.db.refresh(existing)
            self._credit_guide(excursion.guide_id, rating)
            return existing

        created = self.repo.add(
            GuideRating(
                excursion_id=excursion_id,
                guide_id=excursion.guide_id,
                rater_id=principal.user_id,
                rating=rating,
                comment=comment,
            )
        )
        self.db.commit()
        self.db.refresh(created)
        self._credit_guide(excursion.guide_id, rating)
        return created

    @staticmethod
    def _credit_guide(guide_id: str, rating: int) -> None:
        if rating == 5:
            achievement_client.award_achievement(
                user_id=guide_id, code=achievement_client.HISTORIAN_FIVE_STARS
            )

    def for_excursion(self, excursion_id: str) -> list[GuideRating]:
        if self.excursions.get(excursion_id) is None:
            raise NotFound("Экскурсия не найдена")
        return list(self.repo.for_excursion(excursion_id))

    # --- рейтинг краеведов ---

    def ranking(self, period: RatingPeriod = "all") -> Ranking:
        """Все краеведы с оценками за период по местам.

        Место — по байесовскому среднему: к оценкам краеведа добавляем C
        оценок середины шкалы (см. `guide_rating_prior_mean` в настройках).
        Одна пятёрка тогда не обгоняет сорок оценок по 4,8, а с ростом числа
        оценок место всё больше зависит от них самих. Краеведов десятки —
        считаем в Python по сгруппированным в SQL строкам.
        """
        window = PERIOD_WINDOW[period]
        totals = self.repo.totals_by_guide(utcnow() - window if window else None)
        if not totals:
            return Ranking(global_average=0.0, ranks=[])

        prior = settings.guide_rating_prior_weight
        prior_mean = settings.guide_rating_prior_mean
        mean = sum(t.total for t in totals) / sum(t.count for t in totals)

        def score(t: GuideTotals) -> float:
            return (prior * prior_mean + t.total) / (prior + t.count)

        def order(t: GuideTotals) -> tuple:
            last = as_utc(t.last_rated_at).timestamp() if t.last_rated_at else 0.0
            # Равный счёт — выше тот, у кого больше оценок, потом свежее последняя.
            return (-score(t), -t.count, -last, t.guide_id)

        ranks = [
            GuideRank(
                place=place,
                guide_id=t.guide_id,
                average=round(t.total / t.count, 2),
                count=t.count,
                score=round(score(t), 3),
                last_rated_at=as_utc(t.last_rated_at) if t.last_rated_at else None,
            )
            for place, t in enumerate(sorted(totals, key=order), start=1)
        ]
        return Ranking(global_average=round(mean, 2), ranks=ranks)

    def leaderboard(
        self, principal: Principal | None, *, period: RatingPeriod, limit: int, offset: int
    ) -> Leaderboard:
        ranking = self.ranking(period)
        # Места сквозные: на второй странице первое место — пятьдесят первое.
        page = ranking.ranks[offset : offset + limit]
        guide_ids = [rank.guide_id for rank in page]
        profiles = profile_client.profile_briefs(guide_ids) if guide_ids else {}
        led = self.excursions.finished_count_by_guide(guide_ids)
        me = principal.user_id if principal else None
        return Leaderboard(
            period=period,
            global_average=ranking.global_average,
            prior_weight=settings.guide_rating_prior_weight,
            prior_mean=settings.guide_rating_prior_mean,
            total=len(ranking.ranks),
            entries=[
                LeaderboardEntry(
                    rank=rank,
                    profile=profiles.get(rank.guide_id),
                    excursions_led=led.get(rank.guide_id, 0),
                    is_me=rank.guide_id == me,
                )
                for rank in page
            ],
        )

    def guide_card(self, guide_id: str) -> GuideCardView:
        """Карточка краеведа: оценки, место за всё время, отзывы с именами.
        Краевед без оценок — тоже карточка, а не 404: к нему можно записаться."""
        average, count = self.repo.summary_for_guide(guide_id)
        recent = list(self.repo.recent_for_guide(guide_id))
        ranking = self.ranking("all")
        mine = next((rank for rank in ranking.ranks if rank.guide_id == guide_id), None)

        profiles = profile_client.profile_briefs([guide_id, *(r.rater_id for r in recent)])
        titles = self.excursions.titles(r.excursion_id for r in recent)
        reviews = []
        for rating in recent:
            rater = profiles.get(rating.rater_id)
            reviews.append(
                ReviewView(
                    rating=rating,
                    rater_name=rater.display_name if rater and rater.display_name else FALLBACK_RATER_NAME,
                    rater_avatar_url=rater.avatar_url if rater else None,
                    excursion_title=titles.get(rating.excursion_id, ""),
                )
            )

        distribution = {str(stars): 0 for stars in range(1, 6)}
        for stars, stars_count in self.repo.distribution(guide_id).items():
            distribution[str(stars)] = stars_count

        return GuideCardView(
            guide_id=guide_id,
            average=average,
            count=count,
            recent=reviews,
            score=mine.score if mine else None,
            place=mine.place if mine else None,
            total_ranked=len(ranking.ranks),
            excursions_led=self.excursions.finished_count_by_guide([guide_id]).get(guide_id, 0),
            distribution=distribution,
            profile=profiles.get(guide_id),
        )
