from datetime import UTC, datetime, timedelta

import pytest
from conftest import auth_header

from core.db import SessionLocal
from core.models import ExcursionParticipant, ExcursionStatus

SITE = {"lat": 52.967986, "lon": 36.078488}

GUIDE = "guide-1"
VISITOR = "visitor-1"


@pytest.fixture()
def guide_header():
    return auth_header(user_id=GUIDE, role="local_historian")


@pytest.fixture()
def visitor_header():
    return auth_header(user_id=VISITOR)


def make_excursion(client, header, **over):
    body = {
        "title": "Тропа памяти: площадь Мира",
        "place_name": "Площадь Мира, Орёл",
        "starts_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "capacity": 5,
        **SITE,
    }
    body.update(over)
    return client.post("/excursions", headers=header, json=body).json()


def _mark_checked_in(excursion_id: str, user_id: str) -> None:
    """Тест рейтинга не про бамп — отмечаем участника пришедшим напрямую в БД."""
    db = SessionLocal()
    try:
        participant = (
            db.query(ExcursionParticipant)
            .filter_by(excursion_id=excursion_id, user_id=user_id)
            .one()
        )
        participant.checked_in_at = datetime.now(UTC)
        db.commit()
    finally:
        db.close()


def finished_excursion_with_attendee(client, guide_header, visitor_header, *, attended=True):
    excursion = make_excursion(client, guide_header)
    client.post(f"/excursions/{excursion['id']}/registrations", headers=visitor_header)
    if attended:
        _mark_checked_in(excursion["id"], VISITOR)

    # Сбор нужно сначала открыть, стоя на месте, потом можно завершить.
    client.post(f"/excursions/{excursion['id']}/gathering/start", headers=guide_header, json=SITE)
    finish = client.post(f"/excursions/{excursion['id']}/gathering/finish", headers=guide_header)
    assert finish.json()["status"] == ExcursionStatus.finished.value
    return excursion["id"]


def test_only_attendee_can_rate(client, guide_header, visitor_header):
    excursion_id = finished_excursion_with_attendee(
        client, guide_header, visitor_header, attended=False
    )
    r = client.post(
        f"/excursions/{excursion_id}/rating", headers=visitor_header, json={"rating": 5}
    )
    assert r.status_code == 403


def test_guide_cannot_rate_own_excursion(client, guide_header, visitor_header):
    excursion_id = finished_excursion_with_attendee(client, guide_header, visitor_header)
    r = client.post(f"/excursions/{excursion_id}/rating", headers=guide_header, json={"rating": 5})
    assert r.status_code == 409


def test_cannot_rate_before_finished(client, guide_header, visitor_header):
    excursion = make_excursion(client, guide_header)
    client.post(f"/excursions/{excursion['id']}/registrations", headers=visitor_header)
    _mark_checked_in(excursion["id"], VISITOR)
    r = client.post(
        f"/excursions/{excursion['id']}/rating", headers=visitor_header, json={"rating": 5}
    )
    assert r.status_code == 409


def test_rating_flow_and_guide_summary(client, guide_header, visitor_header):
    excursion_id = finished_excursion_with_attendee(client, guide_header, visitor_header)

    r = client.post(
        f"/excursions/{excursion_id}/rating",
        headers=visitor_header,
        json={"rating": 4, "comment": "Отлично рассказывает"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["guide_id"] == GUIDE
    assert body["rater_id"] == VISITOR

    listed = client.get(f"/excursions/{excursion_id}/rating").json()
    assert len(listed) == 1
    assert listed[0]["rating"] == 4

    summary = client.get(f"/guides/{GUIDE}/rating").json()
    assert summary == {
        "guide_id": GUIDE,
        "average": 4.0,
        "count": 1,
        "recent": listed,
    }


def test_rating_twice_updates_instead_of_duplicating(client, guide_header, visitor_header):
    excursion_id = finished_excursion_with_attendee(client, guide_header, visitor_header)

    client.post(f"/excursions/{excursion_id}/rating", headers=visitor_header, json={"rating": 3})
    second = client.post(
        f"/excursions/{excursion_id}/rating", headers=visitor_header, json={"rating": 5}
    )
    assert second.status_code == 201

    listed = client.get(f"/excursions/{excursion_id}/rating").json()
    assert len(listed) == 1
    assert listed[0]["rating"] == 5


def test_out_of_range_rating_rejected(client, guide_header, visitor_header):
    excursion_id = finished_excursion_with_attendee(client, guide_header, visitor_header)
    r = client.post(
        f"/excursions/{excursion_id}/rating", headers=visitor_header, json={"rating": 6}
    )
    assert r.status_code == 422
