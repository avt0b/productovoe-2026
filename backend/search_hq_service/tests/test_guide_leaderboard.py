"""Рейтинг краеведов: места по байесовскому среднему, карточка краеведа,
напоминание «Оцените экскурсию»."""

from datetime import timedelta

import pytest
from conftest import auth_header
from test_excursions import make_excursion
from test_lost_alerts import KID, LATE, MOM, STRANGER, header, walking_group
from test_ratings import VISITOR, finished_excursion_with_attendee

from core.config import settings
from core.db import SessionLocal
from core.models import Excursion, ExcursionStatus, ExcursionWalk, GuideRating
from core.timeutil import utcnow
from services.profile_client import ProfileBrief

# A — одна пятёрка, B — двадцать оценок со средним 4,8.
GUIDE_A = "guide-a"
GUIDE_B = "guide-b"
GUIDE_C = "guide-c"


def rate(guide_id: str, stars: list[int], *, days_ago: int = 0, title: str = "Тропа памяти") -> str:
    """Оценки прямо в базе: рейтинг не про бамп и сбор, а экскурсию через них
    на каждую оценку не проведёшь. Экскурсия заводится завершённой."""
    with SessionLocal() as db:
        excursion = Excursion(
            guide_id=guide_id,
            title=title,
            lat=52.97,
            lon=36.07,
            starts_at=utcnow() - timedelta(days=days_ago + 1),
            status=ExcursionStatus.finished,
        )
        db.add(excursion)
        db.flush()
        for number, value in enumerate(stars):
            db.add(
                GuideRating(
                    excursion_id=excursion.id,
                    guide_id=guide_id,
                    rater_id=f"rater-{guide_id}-{days_ago}-{number}",
                    rating=value,
                    comment="",
                    created_at=utcnow() - timedelta(days=days_ago),
                )
            )
        db.commit()
        return excursion.id


def bayes(total: int, count: int) -> float:
    prior = settings.guide_rating_prior_weight
    return (prior * settings.guide_rating_prior_mean + total) / (prior + count)


def board(client, **params):
    return client.get("/guides/rating", params=params)


@pytest.fixture()
def profiles(monkeypatch):
    from services import profile_client

    known = {
        GUIDE_B: ProfileBrief("Анна Сергеевна", "https://example.ru/storage/users/b.jpg", "Орёл", "local_historian", True),
        f"rater-{GUIDE_B}-0-0": ProfileBrief("Ирина", None, "Мценск", "family", False),
    }
    monkeypatch.setattr(
        profile_client, "profile_briefs", lambda user_ids: {uid: known[uid] for uid in user_ids if uid in known}
    )


def test_many_good_ratings_beat_a_single_five(client):
    rate(GUIDE_A, [5])
    rate(GUIDE_B, [5] * 16 + [4] * 4)  # среднее 4,8

    body = board(client).json()
    # Почти все оценки высокие: общее среднее 4,81. Априорное среднее по нему
    # подняло бы одну пятёрку выше двадцати оценок — поэтому оно — середина шкалы.
    assert body["period"] == "all"
    assert body["global_average"] == round((5 + 96) / 21, 2)
    assert body["prior_weight"] == 5
    assert body["prior_mean"] == 3.0
    assert body["total"] == 2

    first, second = body["items"]
    assert (first["place"], first["guide_id"]) == (1, GUIDE_B)
    assert (second["place"], second["guide_id"]) == (2, GUIDE_A)
    assert first["average"] == 4.8 and first["count"] == 20
    assert first["score"] == round(bayes(96, 20), 3)
    assert second["average"] == 5.0 and second["score"] == round(bayes(5, 1), 3)
    assert first["last_rated_at"].endswith("Z")


def test_month_counts_only_the_last_30_days(client):
    rate(GUIDE_A, [5], days_ago=40)
    rate(GUIDE_B, [4], days_ago=3)

    month = board(client, period="month").json()
    assert [item["guide_id"] for item in month["items"]] == [GUIDE_B]
    assert month["total"] == 1

    everything = board(client, period="all").json()
    assert {item["guide_id"] for item in everything["items"]} == {GUIDE_A, GUIDE_B}


def test_pages_keep_places_and_total(client):
    rate(GUIDE_A, [5, 5, 5])
    rate(GUIDE_B, [4, 4])
    rate(GUIDE_C, [3])

    page = board(client, limit=1, offset=1).json()
    assert page["total"] == 3
    [item] = page["items"]
    assert (item["place"], item["guide_id"]) == (2, GUIDE_B)


def test_is_me_only_with_a_token(client):
    rate(GUIDE_A, [5])
    rate(GUIDE_B, [4])

    mine = client.get("/guides/rating", headers=auth_header(user_id=GUIDE_B, role="local_historian")).json()
    assert {item["guide_id"]: item["is_me"] for item in mine["items"]} == {GUIDE_A: False, GUIDE_B: True}
    assert not any(item["is_me"] for item in board(client).json()["items"])


def test_names_come_from_profiles_with_fallback(client, profiles):
    rate(GUIDE_A, [5])
    rate(GUIDE_B, [5, 5])

    items = {item["guide_id"]: item for item in board(client).json()["items"]}
    assert items[GUIDE_B]["display_name"] == "Анна Сергеевна"
    assert items[GUIDE_B]["city"] == "Орёл"
    assert items[GUIDE_B]["is_verified"] is True
    assert items[GUIDE_B]["avatar_url"] == "https://example.ru/storage/users/b.jpg"
    no_profile = items[GUIDE_A]
    assert (no_profile["display_name"], no_profile["avatar_url"], no_profile["city"], no_profile["is_verified"]) == (
        "Краевед",
        None,
        "",
        False,
    )


def test_excursions_led_counts_only_finished(client):
    rate(GUIDE_B, [5])
    rate(GUIDE_B, [4])
    # Запланированная экскурсия — ещё не проведена.
    make_excursion(client, auth_header(user_id=GUIDE_B, role="local_historian"))

    [item] = board(client).json()["items"]
    assert item["excursions_led"] == 2


def test_guide_card_matches_the_leaderboard(client, profiles):
    rate(GUIDE_A, [5])
    rate(GUIDE_B, [5, 4, 4], title="Мценск: первогвардейцы")

    card = client.get(f"/guides/{GUIDE_B}/rating").json()
    [leader] = [item for item in board(client).json()["items"] if item["guide_id"] == GUIDE_B]
    assert card["place"] == leader["place"] == 1
    assert card["score"] == leader["score"]
    assert card["total_ranked"] == 2
    assert card["average"] == 4.33 and card["count"] == 3
    assert card["distribution"] == {"1": 0, "2": 0, "3": 0, "4": 2, "5": 1}
    assert card["excursions_led"] == 1
    assert card["profile"] == {
        "display_name": "Анна Сергеевна",
        "avatar_url": "https://example.ru/storage/users/b.jpg",
        "city": "Орёл",
        "role": "local_historian",
        "is_verified": True,
    }
    reviews = {review["rater_id"]: review for review in card["recent"]}
    assert reviews[f"rater-{GUIDE_B}-0-0"]["rater_name"] == "Ирина"
    assert reviews[f"rater-{GUIDE_B}-0-1"]["rater_name"] == "Участник экскурсии"
    assert all(review["excursion_title"] == "Мценск: первогвардейцы" for review in card["recent"])


def test_guide_without_ratings_still_has_a_card(client):
    rate(GUIDE_A, [5])

    card = client.get(f"/guides/{GUIDE_C}/rating")
    assert card.status_code == 200
    body = card.json()
    assert (body["average"], body["count"], body["recent"]) == (0.0, 0, [])
    assert body["score"] is None and body["place"] is None
    assert body["total_ranked"] == 1
    assert body["distribution"] == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}


def test_empty_leaderboard(client):
    assert board(client).json() == {
        "period": "all",
        "global_average": 0.0,
        "prior_weight": 5,
        "prior_mean": 3.0,
        "total": 0,
        "items": [],
    }


def test_excursions_can_be_filtered_by_guide(client):
    mine = make_excursion(client, auth_header(user_id=GUIDE_A, role="local_historian")).json()["id"]
    make_excursion(client, auth_header(user_id=GUIDE_B, role="local_historian"))

    listed = client.get("/excursions", params={"guide_id": GUIDE_A}).json()
    assert [excursion["id"] for excursion in listed] == [mine]


def test_bad_query_is_rejected(client):
    assert board(client, period="week").status_code == 422
    assert board(client, limit=0).status_code == 422
    assert board(client, limit=101).status_code == 422
    assert board(client, offset=-1).status_code == 422


# --- «Оцените экскурсию» ---


@pytest.fixture()
def sent(monkeypatch):
    from services import notify_client

    calls = []
    monkeypatch.setattr(notify_client, "notify_users", lambda **kw: calls.append(kw))
    return calls


def rate_requests(calls):
    return [call for call in calls if call["kind"] == "rate_excursion"]


def test_closing_the_gathering_asks_attendees_to_rate(client, sent):
    guide = auth_header(user_id="guide-1", role="local_historian")
    visitor = auth_header(user_id=VISITOR)
    excursion_id = finished_excursion_with_attendee(client, guide, visitor)

    [call] = rate_requests(sent)
    assert call["user_ids"] == [VISITOR]
    assert call["title"] == "Как прошла экскурсия?"
    assert call["body"] == "Оцените «Тропа памяти: площадь Мира» — по оценкам другие выбирают, к кому идти."
    assert call["payload"] == {"excursion_id": excursion_id}


def test_nobody_came_nobody_is_asked(client, sent):
    guide = auth_header(user_id="guide-1", role="local_historian")
    finished_excursion_with_attendee(client, guide, auth_header(user_id=VISITOR), attended=False)
    assert rate_requests(sent) == []


def test_finished_walk_asks_those_who_came(client, sent):
    excursion_id = walking_group(client)
    sent.clear()
    assert client.post(f"/excursions/{excursion_id}/walk/finish", headers=header("guide-1")).status_code == 200

    [call] = rate_requests(sent)
    assert set(call["user_ids"]) == {KID, MOM, STRANGER}
    assert LATE not in call["user_ids"]


def test_walk_that_ran_out_of_time_asks_too(client, sent):
    excursion_id = walking_group(client)
    sent.clear()
    with SessionLocal() as db:
        walk = db.get(ExcursionWalk, excursion_id)
        walk.started_at = utcnow() - timedelta(hours=settings.walk_duration_hours + 1)
        db.commit()

    client.get(f"/excursions/{excursion_id}/walk", headers=header("guide-1"))
    [call] = rate_requests(sent)
    assert set(call["user_ids"]) == {KID, MOM, STRANGER}
