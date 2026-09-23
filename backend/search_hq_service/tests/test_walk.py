from datetime import timedelta

import pytest
from conftest import auth_header
from test_excursions import (
    GUIDE,
    NEAR,
    VISITOR,
    bump_together,
    make_excursion,
    register,
    start_gathering,
)

from core.config import settings

# Вечный огонь — куда краевед ведёт группу от места сбора.
MEMORIAL = {"lat": 52.9652, "lon": 36.0741, "name": "Вечный огонь", "poi_id": "poi-flame"}


@pytest.fixture()
def guide_header():
    return auth_header(user_id=GUIDE, role="local_historian")


@pytest.fixture()
def visitor_header():
    return auth_header(user_id=VISITOR)


@pytest.fixture()
def sent(monkeypatch):
    """Что ушло в user_service — вместо настоящей рассылки."""
    from services import notify_client

    calls = []
    monkeypatch.setattr(notify_client, "notify_users", lambda **kw: calls.append(kw))
    return calls


def gathered(client, guide_header, visitor_header, *also_registered):
    """Экскурсия, где участник уже отметился бампом.

    `also_registered` — записавшиеся, но не пришедшие: записать их можно только
    до открытия сбора, потом запись закрыта.
    """
    excursion_id = make_excursion(client, guide_header, capacity=5).json()["id"]
    for header in (visitor_header, *also_registered):
        assert register(client, header, excursion_id).status_code == 201
    assert start_gathering(client, guide_header, excursion_id).status_code == 200
    guide_bump, visitor_bump = bump_together(
        client, (guide_header, excursion_id, {}), (visitor_header, excursion_id, {})
    )
    assert visitor_bump.json()["result"] == "matched"
    return excursion_id


def lead(client, header, excursion_id, **over):
    return client.post(f"/excursions/{excursion_id}/walk", headers=header, json={**MEMORIAL, **over})


def report(client, header, excursion_id, where=NEAR):
    return client.put(f"/excursions/{excursion_id}/walk/position", headers=header, json=where)


def test_guide_leads_the_gathered_group_and_calls_it_to_the_map(
    client, guide_header, visitor_header, sent
):
    # Записался, но не пришёл: карта и уведомление не для него.
    latecomer = auth_header(user_id="visitor-late")
    excursion_id = gathered(client, guide_header, visitor_header, latecomer)
    sent.clear()

    r = lead(client, guide_header, excursion_id)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "walking"
    assert body["destination"] == {
        "lat": MEMORIAL["lat"],
        "lon": MEMORIAL["lon"],
        "name": "Вечный огонь",
        "poi_id": "poi-flame",
    }
    assert body["started_at"] is not None

    assert len(sent) == 1
    assert sent[0]["user_ids"] == [VISITOR]
    assert sent[0]["kind"] == "excursion_walk_started"
    assert "Вечный огонь" in sent[0]["body"]

    excursion = client.get(f"/excursions/{excursion_id}", headers=visitor_header).json()
    assert excursion["status"] == "walking"


def test_changing_destination_does_not_wake_everyone_again(client, guide_header, visitor_header, sent):
    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)
    sent.clear()

    r = lead(client, guide_header, excursion_id, lat=52.9700, lon=36.0800, name="Танк Т-34", poi_id=None)
    assert r.status_code == 200
    assert r.json()["destination"]["name"] == "Танк Т-34"
    assert r.json()["destination"]["poi_id"] is None
    assert sent == []


def test_group_cannot_leave_before_gathering(client, guide_header):
    excursion_id = make_excursion(client, guide_header).json()["id"]
    r = lead(client, guide_header, excursion_id)
    assert r.status_code == 409


def test_only_the_guide_leads(client, guide_header, visitor_header):
    excursion_id = gathered(client, guide_header, visitor_header)
    assert lead(client, visitor_header, excursion_id).status_code == 403


def test_everyone_in_the_group_sees_each_other(client, guide_header, visitor_header):
    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)

    assert report(client, guide_header, excursion_id, {"lat": 52.9681, "lon": 36.0786, "accuracy_m": 5}).status_code == 204
    assert report(client, visitor_header, excursion_id, {"lat": 52.9683, "lon": 36.0788}).status_code == 204

    mine = client.get(f"/excursions/{excursion_id}/walk", headers=visitor_header).json()
    assert mine["is_guide"] is False
    members = mine["members"]
    # Краевед — первым, чтобы клиенту не искать его в списке.
    assert [m["user_id"] for m in members] == [GUIDE, VISITOR]
    assert members[0]["is_guide"] is True and members[0]["is_me"] is False
    assert members[0]["accuracy_m"] == 5
    assert members[1]["is_me"] is True

    guides = client.get(f"/excursions/{excursion_id}/walk", headers=guide_header).json()
    assert guides["is_guide"] is True
    assert [m["is_me"] for m in guides["members"]] == [True, False]


def test_second_report_moves_the_point_instead_of_adding_one(client, guide_header, visitor_header):
    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)

    report(client, visitor_header, excursion_id, {"lat": 52.9683, "lon": 36.0788})
    report(client, visitor_header, excursion_id, {"lat": 52.9690, "lon": 36.0790})

    members = client.get(f"/excursions/{excursion_id}/walk", headers=visitor_header).json()["members"]
    assert len(members) == 1
    assert members[0]["lat"] == pytest.approx(52.9690)


def test_stale_points_are_not_shown(client, guide_header, visitor_header, monkeypatch):
    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)
    report(client, visitor_header, excursion_id)

    import services.walk_service as walk_module

    real_now = walk_module.utcnow
    later = real_now() + timedelta(seconds=settings.walk_position_ttl_seconds + 5)
    monkeypatch.setattr(walk_module, "utcnow", lambda: later)

    members = client.get(f"/excursions/{excursion_id}/walk", headers=guide_header).json()["members"]
    assert members == []


def test_map_is_only_for_those_who_actually_came(client, guide_header, visitor_header):
    # Записался, но не отметился бампом.
    latecomer = auth_header(user_id="visitor-late")
    excursion_id = gathered(client, guide_header, visitor_header, latecomer)
    lead(client, guide_header, excursion_id)

    r = client.get(f"/excursions/{excursion_id}/walk", headers=latecomer)
    assert r.status_code == 403
    assert "отметьтесь" in r.json()["detail"]
    assert report(client, latecomer, excursion_id).status_code == 403

    stranger = auth_header(user_id="stranger")
    assert client.get(f"/excursions/{excursion_id}/walk", headers=stranger).status_code == 403


def test_positions_only_while_walking(client, guide_header, visitor_header):
    excursion_id = gathered(client, guide_header, visitor_header)
    # Сбор идёт, группа ещё не вышла — точку показывать некому.
    assert report(client, visitor_header, excursion_id).status_code == 409


def test_finish_ends_the_walk_and_forgets_where_people_were(client, guide_header, visitor_header):
    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)
    report(client, visitor_header, excursion_id)

    r = client.post(f"/excursions/{excursion_id}/walk/finish", headers=guide_header)
    assert r.status_code == 200
    assert r.json()["status"] == "finished"
    assert r.json()["members"] == []

    assert report(client, visitor_header, excursion_id).status_code == 409
    # Повторное «Завершить» — не ошибка.
    assert client.post(f"/excursions/{excursion_id}/walk/finish", headers=guide_header).status_code == 200


def test_walk_ends_by_itself_when_the_guide_forgets(client, guide_header, visitor_header, monkeypatch):
    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)

    import services.walk_service as walk_module

    later = walk_module.utcnow() + timedelta(hours=settings.walk_duration_hours, minutes=1)
    monkeypatch.setattr(walk_module, "utcnow", lambda: later)

    r = client.get(f"/excursions/{excursion_id}/walk", headers=visitor_header)
    assert r.json()["status"] == "finished"


def test_finished_walk_counts_in_profile_stats(client, guide_header, visitor_header, monkeypatch):
    """Экскурсия, дошедшая до памятника, — самая настоящая завершённая: в
    статистику профиля она идёт краеведу и пришедшим, ровно один раз."""
    import services.stats_client as stats_client_module

    credited = []
    monkeypatch.setattr(
        stats_client_module, "increment_stat", lambda **kw: credited.append((kw["user_id"], kw["metric"]))
    )

    excursion_id = gathered(client, guide_header, visitor_header)
    lead(client, guide_header, excursion_id)
    # Выход группы — ещё не завершение.
    assert credited == []

    client.post(f"/excursions/{excursion_id}/walk/finish", headers=guide_header)
    assert sorted(credited) == sorted([(GUIDE, "excursions_completed"), (VISITOR, "excursions_completed")])

    # Повторное «Завершить» не засчитывает второй раз.
    client.post(f"/excursions/{excursion_id}/walk/finish", headers=guide_header)
    assert len(credited) == 2
