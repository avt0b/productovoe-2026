"""Тесты служебной плоскости /internal/* (используется admin_service)."""

import uuid

from conftest import auth_header

from core.config import settings

INTERNAL_HEADERS = {"X-Internal-Key": settings.internal_api_key}
WRONG_HEADERS = {"X-Internal-Key": "not-the-real-key"}

KRUPYSHINO = {"lat": 52.74, "lon": 35.97}


def make_point(client, header, **over):
    body = {
        "soldier_name": "Красноармеец Иванов И.И.",
        "unit": "9-я воздушно-десантная бригада",
        "lat": KRUPYSHINO["lat"],
        "lon": KRUPYSHINO["lon"],
        "circumstances": "Овраг у д. Крупышино, октябрь 1941",
        "date_text": "октябрь 1941",
        "source": "Книга Памяти, Т. 5",
    }
    body.update(over)
    return client.post("/last-stand", headers=header, json=body)


def make_poi(client, header, **over):
    body = {
        "kind": "monument",
        "title": "Памятник морякам ТОФ",
        "description": "с. Крупышино, Кромской район",
        "lat": KRUPYSHINO["lat"],
        "lon": KRUPYSHINO["lon"],
        "date_text": "1943",
        "source": "Книга Памяти, Т. 5",
    }
    body.update(over)
    return client.post("/poi", headers=header, json=body)


# --- доступ по ключу -------------------------------------------------


def test_stats_without_key_403(client):
    r = client.get("/internal/stats")
    assert r.status_code == 403
    assert r.json()["detail"] == "Недействительный внутренний ключ"


def test_stats_with_wrong_key_403(client):
    assert client.get("/internal/stats", headers=WRONG_HEADERS).status_code == 403


def test_timeseries_without_key_403(client):
    assert client.get("/internal/stats/timeseries").status_code == 403


def test_last_stand_list_without_key_403(client):
    assert client.get("/internal/last-stand").status_code == 403


def test_last_stand_status_without_key_403(client):
    r = client.patch("/internal/last-stand/whatever/status", json={"status": "archive_confirmed"})
    assert r.status_code == 403


def test_last_stand_delete_without_key_403(client):
    assert client.delete("/internal/last-stand/whatever").status_code == 403


def test_poi_list_without_key_403(client):
    assert client.get("/internal/poi").status_code == 403


def test_poi_delete_without_key_403(client):
    assert client.delete("/internal/poi/whatever").status_code == 403


def test_poi_delete_with_wrong_key_403(client):
    assert client.delete("/internal/poi/whatever", headers=WRONG_HEADERS).status_code == 403


# --- /internal/stats -----------------------------------------------------


def test_stats_shape(client):
    make_poi(client, auth_header(role="local_historian"), kind="grave")
    make_poi(client, auth_header(role="local_historian"), kind="monument")

    p1 = make_point(client, auth_header(role="searcher")).json()
    make_point(client, auth_header(role="searcher"))
    client.patch(
        f"/last-stand/{p1['id']}/status",
        headers=auth_header(role="moderator"),
        json={"status": "archive_confirmed"},
    )

    r = client.get("/internal/stats", headers=INTERNAL_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "map_service"
    assert body["poi_total"] == 2
    assert body["poi_by_kind"]["grave"] == 1
    assert body["poi_by_kind"]["monument"] == 1
    assert body["poi_added_30d"] == 2
    assert body["last_stand_total"] == 2
    assert body["last_stand_by_status"]["archive_confirmed"] == 1
    assert body["last_stand_by_status"]["discovered"] == 1
    assert body["last_stand_unconfirmed"] == 1
    assert body["last_stand_added_7d"] == 2


def test_timeseries_shape(client):
    make_point(client, auth_header(role="searcher"))
    make_point(client, auth_header(role="searcher"))

    r = client.get("/internal/stats/timeseries", headers=INTERNAL_HEADERS, params={"days": 7})
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "map_service"
    assert body["days"] == 7
    assert isinstance(body["points"], list)
    assert sum(p["value"] for p in body["points"]) == 2
    assert all("date" in p for p in body["points"])


# --- /internal/last-stand -------------------------------------------------


def test_last_stand_list_ok_and_filters(client):
    p1 = make_point(
        client, auth_header(role="searcher"), soldier_name="Иванов Иван", unit="9-я бригада"
    ).json()
    p2 = make_point(
        client, auth_header(role="searcher"), soldier_name="Петров Пётр", unit="5-й полк"
    ).json()
    client.patch(
        f"/last-stand/{p1['id']}/status",
        headers=auth_header(role="moderator"),
        json={"status": "archive_confirmed"},
    )

    all_points = client.get("/internal/last-stand", headers=INTERNAL_HEADERS)
    assert all_points.status_code == 200
    body = all_points.json()
    assert body["total"] == 2
    assert body["limit"] == 50
    assert body["offset"] == 0

    by_status = client.get(
        "/internal/last-stand", headers=INTERNAL_HEADERS, params={"status": "archive_confirmed"}
    ).json()
    assert by_status["total"] == 1
    assert by_status["items"][0]["id"] == p1["id"]

    by_query = client.get(
        "/internal/last-stand", headers=INTERNAL_HEADERS, params={"query": "Петров"}
    ).json()
    assert by_query["total"] == 1
    assert by_query["items"][0]["id"] == p2["id"]


def test_last_stand_status_update_bypasses_moderator_only(client):
    point = make_point(client, auth_header(role="searcher")).json()

    # публично статус меняет только модератор
    assert (
        client.patch(
            f"/last-stand/{point['id']}/status",
            headers=auth_header(role="searcher"),
            json={"status": "archive_confirmed"},
        ).status_code
        == 403
    )

    # через внутренний ключ — независимо от роли актора
    r = client.patch(
        f"/internal/last-stand/{point['id']}/status",
        headers={**INTERNAL_HEADERS, "X-Actor-Id": "admin-9"},
        json={"status": "archive_confirmed"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "archive_confirmed"

    # видно и через внутренний, и через публичный GET
    assert (
        client.get(
            "/internal/last-stand", headers=INTERNAL_HEADERS, params={"query": "Иванов"}
        ).json()["items"][0]["status"]
        == "archive_confirmed"
    )
    assert client.get(f"/last-stand/{point['id']}").json()["status"] == "archive_confirmed"


def test_last_stand_status_update_missing_404(client):
    r = client.patch(
        f"/internal/last-stand/{uuid.uuid4()}/status",
        headers=INTERNAL_HEADERS,
        json={"status": "archive_confirmed"},
    )
    assert r.status_code == 404


def test_last_stand_delete_bypasses_ownership(client):
    creator = str(uuid.uuid4())
    point = make_point(client, auth_header(user_id=creator, role="searcher")).json()

    # публично удалить может только автор или модератор
    assert (
        client.delete(
            f"/last-stand/{point['id']}", headers=auth_header(role="searcher")
        ).status_code
        == 403
    )

    r = client.delete(
        f"/internal/last-stand/{point['id']}",
        headers={**INTERNAL_HEADERS, "X-Actor-Id": "someone-else"},
    )
    assert r.status_code == 204
    assert client.get(f"/last-stand/{point['id']}").status_code == 404


def test_last_stand_delete_missing_404(client):
    r = client.delete(f"/internal/last-stand/{uuid.uuid4()}", headers=INTERNAL_HEADERS)
    assert r.status_code == 404


# --- /internal/poi ---------------------------------------------------------


def test_poi_list_ok_and_filters(client):
    p1 = make_poi(
        client, auth_header(role="local_historian"), kind="grave", title="Братская могила"
    )
    p2 = make_poi(
        client, auth_header(role="local_historian"), kind="monument", title="Памятник танкистам"
    )
    poi1, poi2 = p1.json(), p2.json()

    all_poi = client.get("/internal/poi", headers=INTERNAL_HEADERS)
    assert all_poi.status_code == 200
    body = all_poi.json()
    assert body["total"] == 2

    by_kind = client.get("/internal/poi", headers=INTERNAL_HEADERS, params={"kind": "grave"}).json()
    assert by_kind["total"] == 1
    assert by_kind["items"][0]["id"] == poi1["id"]

    by_query = client.get(
        "/internal/poi", headers=INTERNAL_HEADERS, params={"query": "танкистам"}
    ).json()
    assert by_query["total"] == 1
    assert by_query["items"][0]["id"] == poi2["id"]


def test_poi_delete_bypasses_ownership(client):
    creator = str(uuid.uuid4())
    poi = make_poi(client, auth_header(user_id=creator, role="local_historian")).json()

    # публично удалить может только автор или модератор
    assert client.delete(f"/poi/{poi['id']}", headers=auth_header(role="family")).status_code == 403

    r = client.delete(
        f"/internal/poi/{poi['id']}", headers={**INTERNAL_HEADERS, "X-Actor-Id": "someone-else"}
    )
    assert r.status_code == 204
    assert client.get(f"/poi/{poi['id']}").status_code == 404


def test_poi_delete_missing_404(client):
    r = client.delete(f"/internal/poi/{uuid.uuid4()}", headers=INTERNAL_HEADERS)
    assert r.status_code == 404
