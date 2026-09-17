"""Тесты `api/routers/operations.py`: права (`viewer` vs write-роли), реальная
передача вызова в `Upstream` (сервис/метод/путь/actor_id/params/json),
запись в аудит, и что при недоступности сервиса вниз возвращается осмысленная
ошибка, а не 500 — и аудит в этом случае не пишется (см. код: `audit.record`
вызывается только ПОСЛЕ успешного `upstream.call`, так что при исключении
до него запись просто не создаётся).

Полный перебор всех 20+ ручек не требуется — по одному-два эндпоинта на
раздел, с одним и тем же набором проверок.
"""

import pytest
from conftest import auth_headers
from helpers import create_admin

from core.models import AdminRole

# fake_upstream — фикстура из tests/conftest.py, доступна без импорта.

WRITE_ROLES = [AdminRole.superadmin, AdminRole.admin, AdminRole.moderator]


def _headers_for(client, superadmin, role: AdminRole):
    """Возвращает (actor, headers) для роли — superadmin уже есть в фикстуре."""
    if role is AdminRole.superadmin:
        return superadmin, auth_headers(client)
    email = f"{role.value}@marshruty.ru"
    password = f"{role.value}-strong-pass-1"
    actor = create_admin(email, password, role)
    return actor, auth_headers(client, email=email, password=password)


def _viewer_headers(client, suffix: str = ""):
    email = f"viewer{suffix}@marshruty.ru"
    password = "viewer-strong-pass-1"
    create_admin(email, password, AdminRole.viewer)
    return auth_headers(client, email=email, password=password)


# --- Пользователи и роли ----------------------------------------------------


def test_list_users_is_readable_by_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    fake_upstream.set_response(
        "auth", "GET", "/internal/users", {"items": [], "total": 0}
    )
    response = client.get("/admin/ops/users", headers=headers)
    assert response.status_code == 200
    call = fake_upstream.calls[0]
    assert call["service"] == "auth"
    assert call["method"] == "GET"
    assert call["path"] == "/internal/users"
    assert call["params"] == {"limit": 50, "offset": 0}


def test_set_user_role_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.patch(
        "/admin/ops/users/u1/role", headers=headers, json={"role": "mentor"}
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_set_user_role_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream, role
):
    actor, headers = _headers_for(client, superadmin, role)
    user_id = "11111111-1111-1111-1111-111111111111"
    fake_upstream.set_response(
        "auth",
        "GET",
        f"/internal/users/{user_id}",
        {"id": user_id, "email": "soldier@example.com", "role": "searcher"},
    )
    fake_upstream.set_response(
        "auth",
        "PATCH",
        f"/internal/users/{user_id}/role",
        {"id": user_id, "email": "soldier@example.com", "role": "mentor"},
    )

    response = client.patch(
        f"/admin/ops/users/{user_id}/role", headers=headers, json={"role": "mentor"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "mentor"

    patch_call = next(c for c in fake_upstream.calls if c["method"] == "PATCH")
    assert patch_call == {
        "service": "auth",
        "method": "PATCH",
        "path": f"/internal/users/{user_id}/role",
        "actor_id": actor.id,
        "params": None,
        "json": {"role": "mentor"},
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "user.role.set"}
    ).json()
    assert audit["total"] == 1
    row = audit["items"][0]
    assert row["target_service"] == "auth_service"
    assert row["target_id"] == user_id
    assert row["actor_email"] == actor.email
    assert row["outcome"] == "success"


def test_set_user_role_upstream_failure_returns_error_and_no_audit(
    client, superadmin, fake_upstream
):
    headers = auth_headers(client)
    user_id = "22222222-2222-2222-2222-222222222222"
    fake_upstream.set_response(
        "auth", "GET", f"/internal/users/{user_id}", {"id": user_id, "role": "searcher"}
    )
    fake_upstream.fail(
        "auth", "PATCH", f"/internal/users/{user_id}/role", detail="auth_service недоступен"
    )

    response = client.patch(
        f"/admin/ops/users/{user_id}/role", headers=headers, json={"role": "mentor"}
    )
    # UpstreamUnavailable — доменная ошибка с кодом 502, а не голый 500.
    assert response.status_code == 502
    assert response.json()["detail"] == "auth_service недоступен"

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "user.role.set"}
    ).json()
    assert audit["total"] == 0


# --- Профили и верификация статуса ------------------------------------------


def test_verify_profile_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.patch(
        "/admin/ops/profiles/p1/verify?is_verified=true", headers=headers, json={"note": ""}
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_verify_profile_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.admin)
    profile_id = "profile-1"
    fake_upstream.set_response(
        "user",
        "PATCH",
        f"/internal/profiles/{profile_id}/verify",
        {"id": profile_id, "display_name": "Иван Краевед", "is_verified": True},
    )

    response = client.patch(
        f"/admin/ops/profiles/{profile_id}/verify?is_verified=true",
        headers=headers,
        json={"note": "документы проверены"},
    )
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    assert call == {
        "service": "user",
        "method": "PATCH",
        "path": f"/internal/profiles/{profile_id}/verify",
        "actor_id": actor.id,
        "params": {"is_verified": True},
        "json": None,
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "profile.verify"}
    ).json()
    assert audit["total"] == 1
    assert audit["items"][0]["target_label"] == "Иван Краевед"


# --- Модерация народного архива ---------------------------------------------


def test_verify_entry_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.post(
        "/admin/ops/entries/e1/verify", headers=headers, json={"note": ""}
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_verify_entry_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.moderator)
    entry_id = "entry-1"
    fake_upstream.set_response(
        "archive",
        "POST",
        f"/internal/entries/{entry_id}/verify",
        {"id": entry_id, "title": "Письмо с фронта"},
    )

    response = client.post(
        f"/admin/ops/entries/{entry_id}/verify",
        headers=headers,
        json={"note": "источник подтверждён"},
    )
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    assert call == {
        "service": "archive",
        "method": "POST",
        "path": f"/internal/entries/{entry_id}/verify",
        "actor_id": actor.id,
        "params": None,
        "json": {"note": "источник подтверждён"},
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "entry.verify"}
    ).json()
    assert audit["total"] == 1
    assert audit["items"][0]["target_service"] == "archive_service"


def test_verify_entry_upstream_failure_returns_error_and_no_audit(
    client, superadmin, fake_upstream
):
    headers = auth_headers(client)
    entry_id = "entry-down"
    fake_upstream.fail(
        "archive",
        "POST",
        f"/internal/entries/{entry_id}/verify",
        detail="archive_service ответил 404",
    )

    response = client.post(
        f"/admin/ops/entries/{entry_id}/verify", headers=headers, json={"note": ""}
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "archive_service ответил 404"

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "entry.verify"}
    ).json()
    assert audit["total"] == 0


# --- Точки «Последнего боя» --------------------------------------------------


def test_set_last_stand_status_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.patch(
        "/admin/ops/last-stand/ls1/status",
        headers=headers,
        json={"status": "archive_confirmed"},
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_set_last_stand_status_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.superadmin)
    point_id = "ls-1"
    fake_upstream.set_response(
        "map",
        "PATCH",
        f"/internal/last-stand/{point_id}/status",
        {"id": point_id, "soldier_name": "Рядовой Иванов", "status": "archive_confirmed"},
    )

    response = client.patch(
        f"/admin/ops/last-stand/{point_id}/status",
        headers=headers,
        json={"status": "archive_confirmed", "reason": "архив подтвердил находку"},
    )
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    assert call == {
        "service": "map",
        "method": "PATCH",
        "path": f"/internal/last-stand/{point_id}/status",
        "actor_id": actor.id,
        "params": None,
        "json": {"status": "archive_confirmed"},
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "last_stand.status.set"}
    ).json()
    assert audit["total"] == 1
    assert audit["items"][0]["target_label"] == "Рядовой Иванов"


# --- Поисковый штаб: отряды, сборы, выезды ----------------------------------


def test_close_need_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.post(
        "/admin/ops/needs/n1/close", headers=headers, json={"reason": ""}
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_close_need_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.admin)
    need_id = "need-1"
    fake_upstream.set_response(
        "search_hq",
        "POST",
        f"/internal/needs/{need_id}/close",
        {"id": need_id, "title": "Сбор на металлоискатель"},
    )

    response = client.post(
        f"/admin/ops/needs/{need_id}/close",
        headers=headers,
        json={"reason": "цель достигнута"},
    )
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    # `reason` уходит только в аудит-лог, не передаётся в апстрим.
    assert call == {
        "service": "search_hq",
        "method": "POST",
        "path": f"/internal/needs/{need_id}/close",
        "actor_id": actor.id,
        "params": None,
        "json": None,
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "need.close"}
    ).json()
    assert audit["total"] == 1
    assert "цель достигнута" in audit["items"][0]["message"]


# --- Маршруты ----------------------------------------------------------------


def test_publish_route_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.post(
        "/admin/ops/routes/r1/publish", headers=headers, json={"is_published": True}
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_publish_route_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.moderator)
    route_id = "route-1"
    fake_upstream.set_response(
        "route",
        "POST",
        f"/internal/routes/{route_id}/publish",
        {"id": route_id, "title": "Тропой поиска", "is_published": True},
    )

    response = client.post(
        f"/admin/ops/routes/{route_id}/publish",
        headers=headers,
        json={"is_published": True},
    )
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    assert call == {
        "service": "route",
        "method": "POST",
        "path": f"/internal/routes/{route_id}/publish",
        "actor_id": actor.id,
        "params": None,
        "json": {"is_published": True},
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "route.publish"}
    ).json()
    assert audit["total"] == 1
    assert audit["items"][0]["target_label"] == "Тропой поиска"


# --- «Живое фото»: retry / visibility ----------------------------------------


def test_retry_clip_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.post("/admin/ops/clips/c1/retry", headers=headers)
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_retry_clip_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.admin)
    clip_id = "clip-1"
    fake_upstream.set_response(
        "media",
        "POST",
        f"/internal/clips/{clip_id}/retry",
        {"id": clip_id, "soldier_name": "Сержант Петров", "status": "queued"},
    )

    response = client.post(f"/admin/ops/clips/{clip_id}/retry", headers=headers)
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    assert call == {
        "service": "media",
        "method": "POST",
        "path": f"/internal/clips/{clip_id}/retry",
        "actor_id": actor.id,
        "params": None,
        "json": None,
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "clip.retry"}
    ).json()
    assert audit["total"] == 1
    assert audit["items"][0]["target_label"] == "Сержант Петров"


def test_retry_clip_upstream_failure_returns_error_and_no_audit(
    client, superadmin, fake_upstream
):
    headers = auth_headers(client)
    clip_id = "clip-down"
    fake_upstream.fail(
        "media", "POST", f"/internal/clips/{clip_id}/retry", detail="media_service недоступен"
    )

    response = client.post(f"/admin/ops/clips/{clip_id}/retry", headers=headers)
    assert response.status_code == 502
    assert response.json()["detail"] == "media_service недоступен"

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "clip.retry"}
    ).json()
    assert audit["total"] == 0


def test_set_clip_visibility_forbidden_for_viewer(client, superadmin, fake_upstream):
    headers = _viewer_headers(client)
    response = client.patch(
        "/admin/ops/clips/c1/visibility", headers=headers, json={"is_public": False}
    )
    assert response.status_code == 403
    assert fake_upstream.calls == []


def test_set_clip_visibility_success_calls_upstream_and_writes_audit(
    client, superadmin, fake_upstream
):
    actor, headers = _headers_for(client, superadmin, AdminRole.superadmin)
    clip_id = "clip-2"
    fake_upstream.set_response(
        "media",
        "PATCH",
        f"/internal/clips/{clip_id}",
        {"id": clip_id, "soldier_name": "Ефрейтор Сидоров", "is_public": False},
    )

    response = client.patch(
        f"/admin/ops/clips/{clip_id}/visibility",
        headers=headers,
        json={"is_public": False, "reason": "жалоба родственников"},
    )
    assert response.status_code == 200

    call = fake_upstream.calls[0]
    assert call == {
        "service": "media",
        "method": "PATCH",
        "path": f"/internal/clips/{clip_id}",
        "actor_id": actor.id,
        "params": None,
        "json": {"is_public": False},
    }

    audit = client.get(
        "/admin/audit", headers=headers, params={"action": "clip.visibility.set"}
    ).json()
    assert audit["total"] == 1
    assert "жалоба родственников" in audit["items"][0]["message"]
