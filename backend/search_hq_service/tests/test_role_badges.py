from datetime import UTC, datetime, timedelta

import pytest
from conftest import auth_header

GUIDE = auth_header(user_id="guide-1", role="local_historian")
SITE = {"lat": 52.967986, "lon": 36.078488}


@pytest.fixture()
def awarded(monkeypatch):
    import services.achievement_client as achievement_client_module

    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        achievement_client_module,
        "award_achievement",
        lambda *, user_id, code: calls.append((user_id, code)),
    )
    return calls


def test_searcher_badges_for_squad_trip_and_full_fund(client, leader_header, awarded):
    squad = client.post("/squads", headers=leader_header, json={"name": "Высота", "region": "Орёл"}).json()
    client.post(
        f"/squads/{squad['id']}/trips",
        headers=leader_header,
        json={"title": "Разведка", "starts_on": (datetime.now(UTC).date() + timedelta(days=3)).isoformat()},
    )
    need = client.post(
        f"/squads/{squad['id']}/needs",
        headers=leader_header,
        json={"kind": "funds", "title": "ГСМ", "target_amount": 1000},
    ).json()
    client.post(f"/needs/{need['id']}/donations", headers=auth_header(), json={"amount": 400})
    assert ("leader-1", "searcher_goal_reached") not in awarded
    client.post(f"/needs/{need['id']}/donations", headers=auth_header(), json={"amount": 600})

    assert ("leader-1", "searcher_squad_founder") in awarded
    assert ("leader-1", "searcher_trip_organizer") in awarded
    assert awarded.count(("leader-1", "searcher_goal_reached")) == 1


def test_museum_is_not_a_squad_founder_badge(client, awarded):
    client.post(
        "/squads",
        headers=GUIDE,
        json={"name": "Военно-исторический музей", "kind": "museum", "region": "Орёл"},
    )
    assert ("guide-1", "searcher_squad_founder") not in awarded


def test_historian_badges_for_excursion_walk_and_five_stars(client, awarded):
    starts = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    excursion = client.post(
        "/excursions", headers=GUIDE, json={"title": "Тропа", "starts_at": starts, "capacity": 5, **SITE}
    ).json()
    path = f"/excursions/{excursion['id']}"
    client.post(f"{path}/gathering/start", headers=GUIDE, json={**SITE, "accuracy_m": 5})

    client.post(f"{path}/walk", headers=GUIDE, json={**SITE, "name": "Вечный огонь"})
    assert ("guide-1", "historian_led_group") in awarded
    client.post(f"{path}/walk", headers=GUIDE, json={**SITE, "name": "Танк"})
    assert awarded.count(("guide-1", "historian_led_group")) == 1  # только первый выход группы

    assert client.post(f"{path}/walk/finish", headers=GUIDE).status_code == 200
    assert ("guide-1", "historian_first_excursion") in awarded
