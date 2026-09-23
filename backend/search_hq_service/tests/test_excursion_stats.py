from datetime import UTC, datetime, timedelta

import pytest
from conftest import auth_header

import services.excursion_service as excursion_service_module
from services.bump_matcher import bump_matcher

SITE = {"lat": 52.967986, "lon": 36.078488}
NEAR = {"lat": 52.9682, "lon": 36.0787}

GUIDE = "guide-1"


@pytest.fixture()
def guide_header():
    return auth_header(user_id=GUIDE, role="local_historian")


@pytest.fixture()
def stats_spy(monkeypatch):
    calls = []
    monkeypatch.setattr(
        excursion_service_module.stats_client, "increment_stat", lambda **kw: calls.append(kw)
    )
    return calls


@pytest.fixture(autouse=True)
def fast_matcher(monkeypatch):
    monkeypatch.setattr(bump_matcher, "wait_seconds", 0.8)
    bump_matcher.reset()
    yield
    bump_matcher.reset()


def make_excursion(client, header, **over):
    body = {
        "title": "Тропа памяти: площадь Мира",
        "place_name": "Площадь Мира, Орёл",
        "starts_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "capacity": 3,
        **SITE,
    }
    body.update(over)
    return client.post("/excursions", headers=header, json=body)


def register(client, header, excursion_id):
    return client.post(f"/excursions/{excursion_id}/registrations", headers=header)


def start_gathering(client, header, excursion_id):
    return client.post(f"/excursions/{excursion_id}/gathering/start", headers=header, json=SITE)


def bump(client, header, excursion_id):
    return client.post(f"/excursions/{excursion_id}/bumps", headers=header, json=NEAR)


def bump_together(client, guide_header, visitor_header, excursion_id):
    import threading

    results = {}

    def run(key, header):
        results[key] = bump(client, header, excursion_id)

    threads = [
        threading.Thread(target=run, args=("guide", guide_header)),
        threading.Thread(target=run, args=("visitor", visitor_header)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def test_finish_gathering_credits_guide_and_checked_in_participant(client, guide_header, stats_spy):
    visitor = auth_header(user_id="visitor-1")
    excursion = make_excursion(client, guide_header).json()
    register(client, visitor, excursion["id"])
    start_gathering(client, guide_header, excursion["id"])
    bump_together(client, guide_header, visitor, excursion["id"])

    r = client.post(f"/excursions/{excursion['id']}/gathering/finish", headers=guide_header)
    assert r.status_code == 200

    assert {"user_id": GUIDE, "metric": "excursions_completed"} in stats_spy
    assert {"user_id": "visitor-1", "metric": "excursions_completed"} in stats_spy
    assert len(stats_spy) == 2


def test_finish_gathering_does_not_credit_registered_but_not_checked_in(
    client, guide_header, stats_spy
):
    visitor = auth_header(user_id="no-show-1")
    excursion = make_excursion(client, guide_header).json()
    register(client, visitor, excursion["id"])
    start_gathering(client, guide_header, excursion["id"])
    # никто не трясёт телефон — визитёр не отмечается.

    client.post(f"/excursions/{excursion['id']}/gathering/finish", headers=guide_header)

    assert stats_spy == [{"user_id": GUIDE, "metric": "excursions_completed"}]


def test_finishing_twice_does_not_double_credit(client, guide_header, stats_spy):
    excursion = make_excursion(client, guide_header).json()
    start_gathering(client, guide_header, excursion["id"])

    client.post(f"/excursions/{excursion['id']}/gathering/finish", headers=guide_header)
    client.post(f"/excursions/{excursion['id']}/gathering/finish", headers=guide_header)

    assert stats_spy == [{"user_id": GUIDE, "metric": "excursions_completed"}]


def test_auto_expiry_via_read_credits_exactly_once(client, guide_header, stats_spy):
    """Сбор истекает по времени, а закрывается первым же обращением (без
    явного finish) — _close_if_expired, тот же путь, что и у обычного finish."""
    excursion = make_excursion(client, guide_header).json()
    start_gathering(client, guide_header, excursion["id"])

    from core.db import SessionLocal
    from core.models import Excursion

    db = SessionLocal()
    try:
        row = db.get(Excursion, excursion["id"])
        row.gathering_ends_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    # Несколько независимых чтений подряд — статистика должна начислиться один раз.
    client.get(f"/excursions/{excursion['id']}")
    client.get(f"/excursions/{excursion['id']}")
    client.get("/excursions")

    assert stats_spy == [{"user_id": GUIDE, "metric": "excursions_completed"}]
