"""Тесты дашборда: агрегация `all_stats`/`all_health`, деградация сервисов,
доступность viewer-роли.

`Upstream` подменяется через фикстуру `fake_upstream` (см. tests/helpers.py) —
`DashboardService` дёргает `upstream.all_stats()` / `upstream.call()` /
`upstream.all_health()`, поэтому реальная сеть в тестах не нужна.
"""

from conftest import auth_headers
from helpers import create_admin

from core.models import AdminRole

# fake_upstream — фикстура из tests/conftest.py, доступна без импорта.


def _available(title: str, stats: dict) -> dict:
    return {"available": True, "title": title, "stats": stats}


def _unavailable(title: str, error: str = "недоступен (ConnectError)") -> dict:
    return {"available": False, "title": title, "error": error}


def _full_stats() -> dict:
    """Полный набор статистики по всем 7 сервисам, media — «упавший»."""
    return {
        "auth_service": _available(
            "Аутентификация",
            {
                "users_total": 120,
                "registered_7d": 5,
                "users_active": 100,
                "by_role": {"searcher": 50},
            },
        ),
        "user_service": _available(
            "Профили",
            {
                "pending_verification": 7,
                "pending_verification_by_role": {"local_historian": 3, "searcher": 4},
                "verified": 40,
                "subscribed_to_search": 10,
            },
        ),
        "map_service": _available(
            "Карта и «Последний бой»",
            {
                "last_stand_by_status": {
                    "archive_confirmed": 2,
                    "remains_raised": 1,
                    "unverified": 5,
                },
                "last_stand_total": 8,
                "poi_total": 30,
            },
        ),
        "route_service": _available("Маршруты", {"published": 12}),
        "search_hq_service": _available(
            "Поисковый штаб",
            {
                "trips_upcoming": 3,
                "registrations_active": 9,
                "squads_total": 6,
                "funds_collected": 1000,
                "funds_target": 5000,
            },
        ),
        "archive_service": _available(
            "Народный архив", {"moderation_queue": 15, "verified_7d": 4}
        ),
        # Единственный «упавший» сервис — дашборд не должен падать.
        "media_service": _unavailable("«Живое фото»"),
    }


def test_overview_aggregates_and_marks_degraded_service(client, superadmin, fake_upstream):
    headers = auth_headers(client)
    fake_upstream.stats = _full_stats()

    response = client.get("/admin/dashboard/overview", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["degraded"] == ["media_service"]

    tiles = {t["key"]: t for t in body["tiles"]}
    assert tiles["users_total"]["value"] == 120
    assert tiles["users_total"]["hint"] == "+5 за 7 дней"
    assert tiles["role_verification_queue"]["value"] == 7
    assert tiles["moderation_queue"]["value"] == 15
    assert tiles["last_stand_points"]["value"] == 8
    assert tiles["last_stand_points"]["hint"] == "3 подтверждено архивом"
    assert tiles["active_expeditions"]["value"] == 3
    # Упавший сервис отдаёт null, а не падает эндпоинт.
    assert tiles["media_queue"]["value"] is None

    summary = body["summary"]
    assert summary["users_total"] == 120
    assert summary["routes_published"] == 12
    assert summary["squads_total"] == 6
    assert summary["media_queue_depth"] is None

    assert "recent_audit" in body


def test_overview_survives_all_services_down(client, superadmin, fake_upstream):
    """Даже если вообще ничего не ответило, дашборд отдаёт 200, а не 500."""
    headers = auth_headers(client)
    fake_upstream.stats = {
        name: _unavailable(name)
        for name in (
            "auth_service",
            "user_service",
            "map_service",
            "route_service",
            "search_hq_service",
            "archive_service",
            "media_service",
        )
    }

    response = client.get("/admin/dashboard/overview", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert sorted(body["degraded"]) == sorted(fake_upstream.stats.keys())
    for tile in body["tiles"]:
        assert tile["value"] is None


def test_timeseries_only_calls_map_archive_auth(client, superadmin, fake_upstream):
    """Только map/archive/auth поддерживают /internal/stats/timeseries (см. README.md)."""
    headers = auth_headers(client)
    fake_upstream.set_response(
        "map", "GET", "/internal/stats/timeseries", {"points": [{"date": "2026-09-01", "value": 3}]}
    )
    fake_upstream.set_response(
        "archive", "GET", "/internal/stats/timeseries", {"points": [{"date": "2026-09-01", "value": 7}]}
    )
    fake_upstream.set_response(
        "auth", "GET", "/internal/stats/timeseries", {"points": [{"date": "2026-09-01", "value": 2}]}
    )

    response = client.get("/admin/dashboard/timeseries", headers=headers)
    assert response.status_code == 200
    body = response.json()

    called_services = {c["service"] for c in fake_upstream.calls}
    assert called_services == {"map", "archive", "auth"}
    # user/route/search_hq/media не поддерживают этот эндпоинт и не должны дёргаться.
    assert "user" not in called_services
    assert "route" not in called_services
    assert "search_hq" not in called_services
    assert "media" not in called_services

    series_by_key = {s["key"]: s for s in body["series"]}
    assert series_by_key["last_stand_added"]["points"] == [{"date": "2026-09-01", "value": 3}]
    assert series_by_key["entries_verified"]["points"] == [{"date": "2026-09-01", "value": 7}]
    assert series_by_key["registrations"]["points"] == [{"date": "2026-09-01", "value": 2}]


def test_timeseries_degraded_service_returns_empty_series(client, superadmin, fake_upstream):
    headers = auth_headers(client)
    fake_upstream.fail("map", "GET", "/internal/stats/timeseries")
    fake_upstream.set_response("archive", "GET", "/internal/stats/timeseries", {"points": []})
    fake_upstream.set_response("auth", "GET", "/internal/stats/timeseries", {"points": []})

    response = client.get("/admin/dashboard/timeseries", headers=headers)
    assert response.status_code == 200
    series_by_key = {s["key"]: s for s in response.json()["series"]}
    assert series_by_key["last_stand_added"]["points"] == []


def test_health_reports_per_service_status(client, superadmin, fake_upstream):
    headers = auth_headers(client)
    fake_upstream.health = [
        {"service": "auth_service", "title": "Аутентификация", "url": "http://x", "ok": True,
         "status": "ok", "env": "test"},
        {"service": "media_service", "title": "«Живое фото»", "url": "http://y", "ok": False,
         "status": "недоступен (ConnectError)", "env": ""},
    ]

    response = client.get("/admin/dashboard/health", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["healthy"] == 1
    # total считается по реальному реестру сервисов (7), а не по длине фейка.
    assert body["total"] == 7
    statuses = {row["service"]: row["ok"] for row in body["services"]}
    assert statuses == {"auth_service": True, "media_service": False}


def test_viewer_can_read_dashboard(client, superadmin, fake_upstream):
    """AuthedAdmin (не WriteAdmin) — просмотр дашборда доступен и viewer."""
    create_admin("viewer@marshruty.ru", "viewer-strong-pass", AdminRole.viewer)
    viewer_headers = auth_headers(client, email="viewer@marshruty.ru", password="viewer-strong-pass")

    fake_upstream.stats = _full_stats()
    fake_upstream.health = []
    for service in ("map", "archive", "auth"):
        fake_upstream.set_response(service, "GET", "/internal/stats/timeseries", {"points": []})

    assert client.get("/admin/dashboard/overview", headers=viewer_headers).status_code == 200
    assert client.get("/admin/dashboard/timeseries", headers=viewer_headers).status_code == 200
    assert client.get("/admin/dashboard/health", headers=viewer_headers).status_code == 200
