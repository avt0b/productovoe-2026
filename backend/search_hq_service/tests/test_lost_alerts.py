"""«Я потерялся»: тревога на прогулке, поиск семьёй и краеведом."""

from datetime import timedelta

import pytest
from conftest import auth_header
from sqlalchemy import select
from test_excursions import GUIDE, NEAR, make_excursion, register, start_gathering
from test_walk import lead, report

from core.config import settings
from core.db import SessionLocal
from core.geo import distance_m
from core.models import ExcursionParticipant, ExcursionWalk
from core.timeutil import utcnow
from services.profile_client import ProfileBrief

KID = "kid-1"
MOM = "mom-1"
# Папа в семье, но на экскурсию не пошёл: тревога не для него.
DAD = "dad-1"
# В группе, но не семья.
STRANGER = "stranger-1"
# Записался, но не пришёл.
LATE = "late-1"

FAMILY = {KID: [MOM, DAD], MOM: [KID, DAD], DAD: [KID, MOM]}

# ~100 м к северу от NEAR — там мама, когда Маша отстала.
MOM_SPOT = {"lat": 52.9691, "lon": 36.0787, "accuracy_m": 8}

EXCURSION_TITLE = "Тропа памяти: площадь Мира"


def header(user_id: str) -> dict:
    role = "local_historian" if user_id == GUIDE else "family"
    return auth_header(user_id=user_id, role=role)


@pytest.fixture()
def family(monkeypatch):
    from services import family_client

    monkeypatch.setattr(family_client, "family_member_ids", lambda user_id: FAMILY.get(user_id, []))


@pytest.fixture()
def names(monkeypatch):
    from services import profile_client

    briefs = {
        KID: ProfileBrief("Маша", None, "Орёл", "family", False),
        MOM: ProfileBrief("Мама", "https://example.ru/storage/users/mom.jpg", "Орёл", "family", False),
        GUIDE: ProfileBrief("Анна Сергеевна", None, "Орёл", "local_historian", True),
    }
    monkeypatch.setattr(
        profile_client, "profile_briefs", lambda user_ids: {uid: briefs[uid] for uid in user_ids if uid in briefs}
    )


@pytest.fixture()
def sent(monkeypatch):
    from services import notify_client

    calls = []
    monkeypatch.setattr(notify_client, "notify_users", lambda **kw: calls.append(kw))
    return calls


def walking_group(client, *, checked_in=(KID, MOM, STRANGER), registered_only=(LATE,)) -> str:
    """Группа на прогулке. Отметка бампом ставится прямо в базе: бамп здесь
    не проверяется, а трясти пять телефонов в потоках — долго."""
    excursion_id = make_excursion(client, header(GUIDE), capacity=10).json()["id"]
    for user_id in (*checked_in, *registered_only):
        assert register(client, header(user_id), excursion_id).status_code == 201
    assert start_gathering(client, header(GUIDE), excursion_id).status_code == 200
    with SessionLocal() as db:
        for participant in db.scalars(
            select(ExcursionParticipant).where(
                ExcursionParticipant.excursion_id == excursion_id,
                ExcursionParticipant.user_id.in_(checked_in),
            )
        ):
            participant.checked_in_at = utcnow()
        db.commit()
    assert lead(client, header(GUIDE), excursion_id).status_code == 200
    return excursion_id


def raise_lost(client, user_id, excursion_id, **body):
    return client.post(f"/excursions/{excursion_id}/lost", headers=header(user_id), json=body)


def act(client, user_id, alert_id, action):
    return client.post(f"/lost-alerts/{alert_id}/{action}", headers=header(user_id))


def of_kind(calls, kind):
    return [call for call in calls if call["kind"] == kind]


# --- поднять тревогу ---


def test_lost_kid_calls_family_from_the_group_and_the_guide(client, family, names, sent):
    excursion_id = walking_group(client)
    sent.clear()

    r = raise_lost(client, KID, excursion_id, message="  Я у фонтана  ")
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "active"
    assert body["kind"] == "self"
    assert body["my_role"] == "lost"
    assert body["message"] == "Я у фонтана"
    assert body["excursion_title"] == EXCURSION_TITLE
    assert body["lost"]["display_name"] == "Маша"
    assert body["lost"]["is_me"] is True
    assert body["raised_by"] == {"user_id": KID, "display_name": "Маша"}
    assert body["resolved_at"] is None and body["resolved_by"] is None
    # Папа не в группе, чужой человек — не семья: тревога не для них.
    assert {w["user_id"]: w["relation"] for w in body["watchers"]} == {GUIDE: "guide", MOM: "family"}
    assert not any(w["responding"] for w in body["watchers"])

    [call] = sent
    assert call["kind"] == "lost_alert"
    assert set(call["user_ids"]) == {GUIDE, MOM}
    assert call["title"] == "Потерялся участник: Маша"
    assert call["body"] == "Нажмите, чтобы увидеть на карте, где сейчас «Маша», и проложить маршрут."
    assert call["payload"] == {"alert_id": body["id"], "excursion_id": excursion_id}


def test_pressing_again_returns_the_same_alert_without_new_calls(client, family, sent):
    excursion_id = walking_group(client)
    first = raise_lost(client, KID, excursion_id)
    sent.clear()

    again = raise_lost(client, KID, excursion_id)
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert sent == []


def test_cannot_get_lost_outside_the_walk(client):
    # Сбор идёт, группа ещё не вышла.
    excursion_id = make_excursion(client, header(GUIDE), capacity=5).json()["id"]
    assert register(client, header(KID), excursion_id).status_code == 201
    assert start_gathering(client, header(GUIDE), excursion_id).status_code == 200

    r = raise_lost(client, KID, excursion_id)
    assert r.status_code == 409
    assert r.json()["detail"] == "Потеряться можно только во время прогулки группы"

    missing = raise_lost(client, KID, "no-such-excursion")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Экскурсия не найдена"


def test_only_the_group_can_raise_and_the_guide_cannot_get_lost(client):
    excursion_id = walking_group(client)

    late = raise_lost(client, LATE, excursion_id)
    assert late.status_code == 403
    assert late.json()["detail"] == "Сначала отметьтесь у краеведа — встряхните телефоны рядом"

    guide = raise_lost(client, GUIDE, excursion_id)
    assert guide.status_code == 409
    assert guide.json()["detail"] == "Краевед ведёт группу — ему «Я потерялся» не нужно"


def test_mom_reports_the_kid_she_cannot_see(client, family, names, sent):
    excursion_id = walking_group(client)
    sent.clear()

    r = raise_lost(client, MOM, excursion_id, lost_user_id=KID)
    assert r.status_code == 201
    body = r.json()
    assert body["kind"] == "reported"
    assert body["my_role"] == "watcher"
    assert body["raised_by"] == {"user_id": MOM, "display_name": "Мама"}
    watchers = {w["user_id"]: w for w in body["watchers"]}
    assert set(watchers) == {GUIDE, MOM}
    # Кто поднял тревогу, тот уже ищет.
    assert watchers[MOM]["responding"] is True
    assert watchers[GUIDE]["responding"] is False

    [alert_call] = of_kind(sent, "lost_alert")
    assert alert_call["user_ids"] == [GUIDE]
    assert alert_call["title"] == "Ищем участника: Маша"
    assert alert_call["body"] == "Мама не видит «Маша» рядом. Откройте карту — там последняя известная точка."
    [kid_call] = of_kind(sent, "lost_alert_searching")
    assert kid_call["user_ids"] == [KID]
    assert kid_call["title"] == "Вас ищут"
    assert kid_call["body"] == "Мама не видит вас рядом. Оставайтесь на месте — к вам уже идут."


def test_reporting_someone_else_needs_family_or_the_guide(client, family):
    excursion_id = walking_group(client)

    stranger = raise_lost(client, STRANGER, excursion_id, lost_user_id=KID)
    assert stranger.status_code == 403
    assert stranger.json()["detail"] == "Искать можно только членов своей семьи"

    # Краевед ищет любого из группы — даже того, у кого семьи в приложении нет.
    by_guide = raise_lost(client, GUIDE, excursion_id, lost_user_id=STRANGER)
    assert by_guide.status_code == 201
    [watcher] = by_guide.json()["watchers"]
    assert watcher["user_id"] == GUIDE and watcher["relation"] == "guide" and watcher["responding"] is True

    for outsider in (LATE, GUIDE, "nobody"):
        r = raise_lost(client, MOM, excursion_id, lost_user_id=outsider)
        assert r.status_code == 404
        assert r.json()["detail"] == "Этого человека нет в группе"


def test_coordinates_in_the_alert_become_my_position_on_the_group_map(client):
    excursion_id = walking_group(client)

    r = raise_lost(client, KID, excursion_id, lat=NEAR["lat"], lon=NEAR["lon"], accuracy_m=15)
    assert r.status_code == 201
    position = r.json()["lost"]["position"]
    assert (position["lat"], position["lon"], position["accuracy_m"]) == (NEAR["lat"], NEAR["lon"], 15)

    walk = client.get(f"/excursions/{excursion_id}/walk", headers=header(GUIDE)).json()
    kid = next(m for m in walk["members"] if m["user_id"] == KID)
    assert (kid["lat"], kid["lon"]) == (NEAR["lat"], NEAR["lon"])


def test_body_is_validated(client):
    excursion_id = walking_group(client)
    assert raise_lost(client, KID, excursion_id, lat=NEAR["lat"]).status_code == 422
    assert raise_lost(client, KID, excursion_id, message="а" * 201).status_code == 422
    assert raise_lost(client, KID, excursion_id, lat=91, lon=36).status_code == 422
    # Пустое тело и совсем без тела — «Я потерялся» без координат.
    assert client.post(f"/excursions/{excursion_id}/lost", headers=header(KID)).status_code == 201


# --- поиск ---


def test_mom_responds_and_the_kid_learns_who_is_coming(client, family, names, sent):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]
    sent.clear()

    r = act(client, MOM, alert_id, "respond")
    assert r.status_code == 200
    mom = next(w for w in r.json()["watchers"] if w["user_id"] == MOM)
    assert mom["responding"] is True and mom["responded_at"] is not None and mom["is_me"] is True

    [call] = sent
    assert call["kind"] == "lost_alert_responding"
    assert call["user_ids"] == [KID]
    assert call["title"] == "Мама идёт к вам"
    assert call["body"] == "Оставайтесь на месте, если можете. На карте видно, где «Мама»."

    # Повтор — ничего нового.
    assert act(client, MOM, alert_id, "respond").status_code == 200
    assert len(sent) == 1

    for outsider in (KID, STRANGER):
        denied = act(client, outsider, alert_id, "respond")
        assert denied.status_code == 403
        assert denied.json()["detail"] == "Откликнуться могут только семья и краевед"


def test_found_closes_the_search_for_everyone(client, family, names, sent):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]
    sent.clear()

    r = act(client, MOM, alert_id, "resolve")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "found"
    assert body["resolved_by"] == {"user_id": MOM, "display_name": "Мама"}
    assert body["resolved_at"] is not None

    [call] = sent
    assert call["kind"] == "lost_alert_closed"
    assert set(call["user_ids"]) == {KID, GUIDE}
    assert call["title"] == "Нашлись!"
    assert call["body"] == "Поиск участника «Маша» закрыт — все вместе."
    assert call["payload"] == {"alert_id": alert_id, "excursion_id": excursion_id, "status": "found"}

    assert act(client, KID, alert_id, "resolve").status_code == 200
    assert len(sent) == 1
    for action in ("cancel", "respond"):
        closed = act(client, KID if action == "cancel" else MOM, alert_id, action)
        assert closed.status_code == 409
        assert closed.json()["detail"] == "Поиск уже закрыт"

    stranger = act(client, STRANGER, alert_id, "resolve")
    assert stranger.status_code == 403
    assert stranger.json()["detail"] == "Закрыть поиск могут только семья, краевед и тот, кого ищут"


def test_false_alarm_is_cancelled_by_the_lost_one_only(client, family, names, sent):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]
    sent.clear()

    # Мама ищет, но тревогу не поднимала — отбой не её.
    mom = act(client, MOM, alert_id, "cancel")
    assert mom.status_code == 403
    assert mom.json()["detail"] == "Отменить поиск может тот, кого ищут, или тот, кто его начал"

    r = act(client, KID, alert_id, "cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    [call] = sent
    assert call["kind"] == "lost_alert_closed"
    assert set(call["user_ids"]) == {MOM, GUIDE}
    assert call["title"] == "Отбой тревоги"
    assert call["body"] == "Участник «Маша» не потерялся — поиск отменён."
    assert call["payload"]["status"] == "cancelled"

    assert act(client, KID, alert_id, "cancel").status_code == 200
    assert act(client, MOM, alert_id, "resolve").status_code == 409


def test_who_sees_the_alert(client, family):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]

    for user_id, role in ((KID, "lost"), (MOM, "watcher"), (GUIDE, "watcher")):
        r = client.get(f"/lost-alerts/{alert_id}", headers=header(user_id))
        assert r.status_code == 200
        assert r.json()["my_role"] == role
        active = client.get("/lost-alerts/active", headers=header(user_id)).json()
        assert [alert["id"] for alert in active] == [alert_id]

    stranger = client.get(f"/lost-alerts/{alert_id}", headers=header(STRANGER))
    assert stranger.status_code == 403
    assert stranger.json()["detail"] == "Этот поиск видят только семья и краевед"
    assert client.get("/lost-alerts/active", headers=header(STRANGER)).json() == []

    root = client.get(f"/lost-alerts/{alert_id}", headers=auth_header(user_id="root-1", is_root=True))
    assert root.status_code == 200 and root.json()["my_role"] == "observer"

    missing = client.get("/lost-alerts/no-such-alert", headers=header(KID))
    assert missing.status_code == 404 and missing.json()["detail"] == "Поиск не найден"

    # Закрытая тревога не в «активных», но открывается по id — экран покажет «Нашлись».
    act(client, MOM, alert_id, "resolve")
    assert client.get("/lost-alerts/active", headers=header(KID)).json() == []
    assert client.get(f"/lost-alerts/{alert_id}", headers=header(KID)).json()["status"] == "found"


def test_positions_and_distance_put_the_one_who_is_coming_first(client, family):
    excursion_id = walking_group(client)
    assert report(client, header(KID), excursion_id, NEAR).status_code == 204
    assert report(client, header(MOM), excursion_id, MOM_SPOT).status_code == 204
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]
    act(client, MOM, alert_id, "respond")

    body = client.get(f"/lost-alerts/{alert_id}", headers=header(GUIDE)).json()
    assert body["lost"]["position"]["lat"] == NEAR["lat"]
    first, second = body["watchers"]
    assert first["user_id"] == MOM and first["responding"] is True
    expected = round(distance_m(MOM_SPOT["lat"], MOM_SPOT["lon"], NEAR["lat"], NEAR["lon"]))
    assert first["distance_m"] == expected
    assert first["position"]["accuracy_m"] == MOM_SPOT["accuracy_m"]
    # Краевед точку не присылал — ни точки, ни расстояния, и он в конце.
    assert second["user_id"] == GUIDE
    assert second["position"] is None and second["distance_m"] is None


def test_stale_alert_expires_quietly(client, family, sent, monkeypatch):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]
    sent.clear()

    monkeypatch.setattr(settings, "lost_alert_ttl_minutes", 0)
    r = client.get(f"/lost-alerts/{alert_id}", headers=header(KID))
    assert r.json()["status"] == "expired"
    assert r.json()["resolved_by"] is None
    assert client.get("/lost-alerts/active", headers=header(MOM)).json() == []
    assert sent == []


def test_walk_that_ran_out_of_time_closes_its_alerts(client):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]

    with SessionLocal() as db:
        walk = db.get(ExcursionWalk, excursion_id)
        walk.started_at = utcnow() - timedelta(hours=settings.walk_duration_hours + 1)
        db.commit()

    assert client.get(f"/lost-alerts/{alert_id}", headers=header(KID)).json()["status"] == "expired"


def test_guide_cannot_close_the_walk_while_someone_is_lost(client):
    excursion_id = walking_group(client)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]
    blocked = "Кто-то из группы потерялся — сначала найдите его или закройте поиск"

    finish = client.post(f"/excursions/{excursion_id}/walk/finish", headers=header(GUIDE))
    assert finish.status_code == 409 and finish.json()["detail"] == blocked
    cancel = client.post(f"/excursions/{excursion_id}/cancel", headers=header(GUIDE))
    assert cancel.status_code == 409 and cancel.json()["detail"] == blocked

    act(client, GUIDE, alert_id, "resolve")
    assert client.post(f"/excursions/{excursion_id}/walk/finish", headers=header(GUIDE)).status_code == 200


def test_group_map_marks_the_lost_one(client):
    excursion_id = walking_group(client)
    report(client, header(KID), excursion_id, NEAR)
    report(client, header(MOM), excursion_id, MOM_SPOT)
    alert_id = raise_lost(client, KID, excursion_id).json()["id"]

    members = client.get(f"/excursions/{excursion_id}/walk", headers=header(MOM)).json()["members"]
    marks = {m["user_id"]: m["lost_alert_id"] for m in members}
    assert marks == {KID: alert_id, MOM: None}


def test_user_service_down_still_calls_the_guide(client):
    # Заглушки conftest: семьи и профилей нет — как будто user_service лежит.
    excursion_id = walking_group(client)
    body = raise_lost(client, KID, excursion_id).json()

    assert body["lost"]["display_name"] == "Участник группы"
    [watcher] = body["watchers"]
    assert watcher["user_id"] == GUIDE
    assert watcher["display_name"] == "Краевед"
