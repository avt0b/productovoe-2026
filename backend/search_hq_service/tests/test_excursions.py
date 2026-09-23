import threading
from datetime import UTC, datetime, timedelta

import pytest
from conftest import auth_header

from core.config import settings
from services.bump_matcher import BumpMatcher, Shake, bump_matcher
# Импорт до autouse-заглушки из conftest: тесту клиента нужен настоящий.
from services.notify_client import notify_users as real_notify_users

# Братская могила на площади Мира, Орёл — место сбора группы.
SITE = {"lat": 52.967986, "lon": 36.078488}
# ~25 м от места сбора.
NEAR = {"lat": 52.9682, "lon": 36.0787}
# Военно-исторический музей — почти два километра.
FAR = {"lat": 52.953974, "lon": 36.062678}

GUIDE = "guide-1"
VISITOR = "visitor-1"


@pytest.fixture()
def guide_header():
    return auth_header(user_id=GUIDE, role="local_historian")


@pytest.fixture()
def visitor_header():
    return auth_header(user_id=VISITOR)


@pytest.fixture(autouse=True)
def fast_matcher(monkeypatch):
    """Короткое ожидание пары: тест «пары нет» не должен ждать по две секунды."""
    monkeypatch.setattr(bump_matcher, "wait_seconds", 0.8)
    bump_matcher.reset()
    yield
    bump_matcher.reset()


def make_excursion(client, header, **over):
    body = {
        "title": "Тропа памяти: площадь Мира",
        "place_name": "Площадь Мира, Орёл",
        "starts_at": (datetime.now(UTC) + timedelta(hours=2)).isoformat(),
        "capacity": 2,
        **SITE,
    }
    body.update(over)
    return client.post("/excursions", headers=header, json=body)


def register(client, header, excursion_id):
    return client.post(f"/excursions/{excursion_id}/registrations", headers=header)


def start_gathering(client, header, excursion_id, where=SITE):
    return client.post(f"/excursions/{excursion_id}/gathering/start", headers=header, json=where)


def bump(client, header, excursion_id, where=NEAR, **extra):
    return client.post(f"/excursions/{excursion_id}/bumps", headers=header, json={**where, **extra})


def bump_together(client, *shakes):
    """Трясти телефоны одновременно: каждая встряска — `(header, excursion_id, extra)`."""
    responses = [None] * len(shakes)

    def run(index, header, excursion_id, extra):
        responses[index] = bump(client, header, excursion_id, **extra)

    threads = [threading.Thread(target=run, args=(i, *shake)) for i, shake in enumerate(shakes)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return responses


def gathering_excursion(client, guide_header, visitor_header):
    """Экскурсия с одним записавшимся, сбор уже идёт."""
    excursion = make_excursion(client, guide_header).json()
    assert register(client, visitor_header, excursion["id"]).status_code == 201
    assert start_gathering(client, guide_header, excursion["id"]).status_code == 200
    return excursion["id"]


# --- экскурсии и запись ---


def test_only_guides_create_excursions(client, guide_header):
    assert make_excursion(client, auth_header(role="family")).status_code == 403

    created = make_excursion(client, guide_header)
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "scheduled"
    assert body["guide_id"] == GUIDE
    assert body["registered_count"] == 0
    # Дата наружу — всегда в UTC (pydantic пишет это как «Z»), даже если база отдала её без пояса.
    assert body["starts_at"].endswith("Z")


def test_registration_capacity_and_viewer(client, guide_header):
    excursion = make_excursion(client, guide_header, capacity=1).json()

    assert register(client, guide_header, excursion["id"]).status_code == 409
    assert register(client, auth_header(user_id="a"), excursion["id"]).status_code == 201
    # повторная запись идемпотентна, но второго места нет
    assert register(client, auth_header(user_id="a"), excursion["id"]).status_code == 201
    assert register(client, auth_header(user_id="b"), excursion["id"]).status_code == 409

    detail = client.get(f"/excursions/{excursion['id']}", headers=auth_header(user_id="a")).json()
    assert detail["registered_count"] == 1
    assert detail["viewer"] == {"is_guide": False, "registered": True, "checked_in_at": None}
    assert client.get(f"/excursions/{excursion['id']}").json()["viewer"] is None

    mine = client.get("/excursions/mine", headers=auth_header(user_id="a")).json()
    assert [e["id"] for e in mine["joined"]] == [excursion["id"]]


def test_collective_registration_counts_group_size_against_capacity(client, guide_header):
    excursion = make_excursion(client, guide_header, capacity=10).json()
    school = auth_header(user_id="school-1")

    r = client.post(
        f"/excursions/{excursion['id']}/registrations",
        headers=school,
        json={"organization_name": "Школа №5", "group_size": 8},
    )
    assert r.status_code == 201
    participant = r.json()
    assert participant["organization_name"] == "Школа №5"
    assert participant["group_size"] == 8

    detail = client.get(f"/excursions/{excursion['id']}").json()
    assert detail["registered_count"] == 8

    # ещё 3 места не влезут — из 10 занято 8.
    assert (
        client.post(
            f"/excursions/{excursion['id']}/registrations",
            headers=auth_header(user_id="b"),
            json={"group_size": 3},
        ).status_code
        == 409
    )
    # а 2 — влезут ровно впритык.
    assert (
        client.post(
            f"/excursions/{excursion['id']}/registrations",
            headers=auth_header(user_id="c"),
            json={"group_size": 2},
        ).status_code
        == 201
    )

    # школа может поправить размер группы своей же повторной записью.
    r2 = client.post(
        f"/excursions/{excursion['id']}/registrations",
        headers=school,
        json={"organization_name": "Школа №5", "group_size": 6},
    )
    assert r2.status_code == 201
    assert client.get(f"/excursions/{excursion['id']}").json()["registered_count"] == 8


def test_registration_closes_when_gathering_starts(client, guide_header, visitor_header):
    excursion_id = gathering_excursion(client, guide_header, visitor_header)

    assert register(client, auth_header(user_id="late"), excursion_id).status_code == 409
    cancel = client.delete(f"/excursions/{excursion_id}/registrations/me", headers=visitor_header)
    assert cancel.status_code == 409


def test_gathering_starts_only_by_guide_on_site(client, guide_header):
    excursion = make_excursion(client, guide_header).json()

    other_guide = auth_header(user_id="guide-2", role="local_historian")
    assert start_gathering(client, other_guide, excursion["id"]).status_code == 403

    far = start_gathering(client, guide_header, excursion["id"], where=FAR)
    assert far.status_code == 409
    assert "м от места сбора" in far.json()["detail"]

    started = start_gathering(client, guide_header, excursion["id"])
    assert started.status_code == 200
    assert started.json()["is_open"] is True
    assert started.json()["ends_at"] is not None


# --- бамп ---


def test_guide_and_visitor_bump_together(client, guide_header, visitor_header):
    excursion_id = gathering_excursion(client, guide_header, visitor_header)

    guide_bump, visitor_bump = bump_together(
        client, (guide_header, excursion_id, {}), (visitor_header, excursion_id, {})
    )

    assert guide_bump.status_code == visitor_bump.status_code == 200
    assert guide_bump.json()["result"] == "matched"
    assert guide_bump.json()["matched_user_ids"] == [VISITOR]
    assert guide_bump.json()["checked_in_at"] is None
    assert visitor_bump.json()["result"] == "matched"
    assert visitor_bump.json()["matched_user_ids"] == [GUIDE]
    assert visitor_bump.json()["checked_in_at"] is not None

    state = client.get(f"/excursions/{excursion_id}/gathering", headers=guide_header).json()
    assert state["checked_in_count"] == 1
    assert [c["user_id"] for c in state["checked_in"]] == [VISITOR]

    visitor_state = client.get(f"/excursions/{excursion_id}/gathering", headers=visitor_header)
    assert visitor_state.json()["checked_in"] == []
    assert visitor_state.json()["my_checked_in_at"] is not None

    again = bump(client, visitor_header, excursion_id)
    assert again.json()["result"] == "already_checked_in"


def test_shakes_seconds_apart_do_not_match(client, guide_header, visitor_header):
    excursion_id = gathering_excursion(client, guide_header, visitor_header)

    # Участник тряхнул заметно раньше, чем закрылось окно. Разница — от
    # настройки и с запасом: число вроде «3000 мс» при окне в 3 с стоит на самой
    # границе, и тест проходил или падал в зависимости от миллисекунд между потоками.
    too_early_ms = int((settings.bump_window_seconds + 1.5) * 1000)
    guide_bump, visitor_bump = bump_together(
        client,
        (guide_header, excursion_id, {}),
        (visitor_header, excursion_id, {"shaken_ms_ago": too_early_ms}),
    )

    assert guide_bump.json()["result"] == "no_pair"
    assert visitor_bump.json()["result"] == "no_pair"


def test_bump_rules(client, guide_header, visitor_header):
    excursion = make_excursion(client, guide_header).json()
    register(client, visitor_header, excursion["id"])

    # сбор ещё не начат
    assert bump(client, visitor_header, excursion["id"]).status_code == 409

    start_gathering(client, guide_header, excursion["id"])
    # незаписавшихся бамп не отмечает
    assert bump(client, auth_header(user_id="stranger"), excursion["id"]).status_code == 403
    # слишком далеко от места сбора
    assert bump(client, visitor_header, excursion["id"], where=FAR).status_code == 409
    # краевед не тряс — пары нет
    assert bump(client, visitor_header, excursion["id"]).json()["result"] == "no_pair"

    finished = client.post(f"/excursions/{excursion['id']}/gathering/finish", headers=guide_header)
    assert finished.json()["is_open"] is False
    assert bump(client, visitor_header, excursion["id"]).status_code == 409


# --- сопоставление встрясок ---


def test_matcher_pairs_guide_with_participants_only():
    matcher = BumpMatcher(window_seconds=1.5, wait_seconds=0.05)
    now = matcher.now()

    assert matcher.shake(Shake("ex", "a", False, now)) == []
    # участник с участником не совпадает
    assert matcher.shake(Shake("ex", "b", False, now)) == []
    # другая экскурсия не видит этих встрясок
    assert matcher.shake(Shake("other", GUIDE, True, now)) == []

    matched = matcher.shake(Shake("ex", GUIDE, True, now + 1.0))
    assert {shake.user_id for shake in matched} == {"a", "b"}


def test_matcher_forgets_old_shakes():
    clock = [1000.0]
    matcher = BumpMatcher(window_seconds=1.5, wait_seconds=0.01, clock=lambda: clock[0])

    matcher.shake(Shake("ex", "a", False, 1000.0))
    clock[0] += 60
    assert matcher.shake(Shake("ex", GUIDE, True, 1000.5)) == []


def test_gathering_start_notifies_registered_people(client, guide_header, visitor_header, monkeypatch):
    from services import notify_client

    sent = []
    monkeypatch.setattr(notify_client, "notify_users", lambda **kw: sent.append(kw))

    excursion_id = make_excursion(client, guide_header).json()["id"]
    register(client, visitor_header, excursion_id)
    # Записался и передумал — ему о сборе не пишем.
    other = auth_header(user_id="visitor-2")
    register(client, other, excursion_id)
    client.delete(f"/excursions/{excursion_id}/registrations/me", headers=other)

    assert start_gathering(client, guide_header, excursion_id).status_code == 200

    assert len(sent) == 1
    call = sent[0]
    assert call["user_ids"] == [VISITOR]
    assert call["kind"] == "excursion_gathering_started"
    assert call["payload"] == {"excursion_id": excursion_id}
    assert "Площадь Мира" in call["body"]

    # Повторное «Начать сбор» ничего не рассылает: сбор уже идёт.
    start_gathering(client, guide_header, excursion_id)
    assert len(sent) == 1


def test_notify_client_swallows_network_errors(monkeypatch):
    """user_service лежит — открытие сбора не должно падать вместе с ним."""
    import httpx

    def down(*args, **kwargs):
        raise httpx.ConnectError("user_service лежит")

    monkeypatch.setattr(httpx, "post", down)
    # Настоящий клиент, взятый до подмены заглушкой из conftest.
    real_notify_users(user_ids=["visitor-1"], kind="k", title="t", body="b")
