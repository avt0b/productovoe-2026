"""Операции над данными платформы.

Каждый обработчик — тонкий: сходить в `/internal/*` нужного сервиса и записать
строку в журнал аудита. Права проверяются здесь (роли админки), бизнес-правила
остаются в сервисах-владельцах данных.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Query, Response, status

from api.deps import AuditServiceDep, AuthedAdmin, Client, UpstreamDep, WriteAdmin

router = APIRouter(prefix="/admin/ops", tags=["admin: операции"])


def _label(item: dict | None, *keys: str, fallback: str = "") -> str:
    """Человекочитаемая подпись объекта для колонки «Объект» в журнале."""
    if not isinstance(item, dict):
        return fallback
    for key in keys:
        value = item.get(key)
        if value:
            return str(value)
    return fallback or str(item.get("id", ""))


# --- Пользователи и роли ---------------------------------------------------


@router.get("/users", summary="Пользователи платформы")
async def list_users(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    query: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if query:
        params["query"] = query
    if role:
        params["role"] = role
    if is_active is not None:
        params["is_active"] = is_active
    return await upstream.call("auth", "GET", "/internal/users", params=params)


@router.patch("/users/{user_id}/role", summary="Сменить роль пользователя")
async def set_user_role(
    user_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    role: Annotated[str, Body(embed=True)],
) -> dict:
    before = await upstream.call("auth", "GET", f"/internal/users/{user_id}")
    result = await upstream.call(
        "auth",
        "PATCH",
        f"/internal/users/{user_id}/role",
        actor_id=admin.id,
        json={"role": role},
    )
    audit.record(
        admin,
        action="user.role.set",
        target_service="auth_service",
        target_type="user",
        target_id=user_id,
        target_label=_label(result, "email"),
        message=f"Роль: {(before or {}).get('role')} → {role}",
        payload={"before": {"role": (before or {}).get("role")}, "after": {"role": role}},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.patch("/users/{user_id}/active", summary="Включить или заблокировать пользователя")
async def set_user_active(
    user_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    is_active: Annotated[bool, Query()],
    reason: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "auth",
        "PATCH",
        f"/internal/users/{user_id}/active",
        actor_id=admin.id,
        params={"is_active": is_active},
    )
    audit.record(
        admin,
        action="user.active.set",
        target_service="auth_service",
        target_type="user",
        target_id=user_id,
        target_label=_label(result, "email"),
        message=("Доступ восстановлен" if is_active else "Доступ заблокирован")
        + (f". Основание: {reason}" if reason else ""),
        payload={"is_active": is_active, "reason": reason},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.patch("/users/{user_id}/root", summary="Выдать или снять флаг is_root")
async def set_user_root(
    user_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    is_root: Annotated[bool, Query()],
) -> dict:
    result = await upstream.call(
        "auth",
        "PATCH",
        f"/internal/users/{user_id}/root",
        actor_id=admin.id,
        params={"is_root": is_root},
    )
    audit.record(
        admin,
        action="user.root.set",
        target_service="auth_service",
        target_type="user",
        target_id=user_id,
        target_label=_label(result, "email"),
        message="Выдан доступ is_root" if is_root else "Снят доступ is_root",
        payload={"is_root": is_root},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


# --- Профили и верификация статуса ----------------------------------------


@router.get("/profiles", summary="Профили пользователей")
async def list_profiles(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    query: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    is_verified: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if query:
        params["query"] = query
    if role:
        params["role"] = role
    if is_verified is not None:
        params["is_verified"] = is_verified
    return await upstream.call("user", "GET", "/internal/profiles", params=params)


@router.patch("/profiles/{profile_id}/verify", summary="Подтвердить статус краеведа/поисковика")
async def verify_profile(
    profile_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    is_verified: Annotated[bool, Query()],
    note: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "user",
        "PATCH",
        f"/internal/profiles/{profile_id}/verify",
        actor_id=admin.id,
        params={"is_verified": is_verified},
    )
    audit.record(
        admin,
        action="profile.verify",
        target_service="user_service",
        target_type="profile",
        target_id=profile_id,
        target_label=_label(result, "display_name", fallback=profile_id),
        message=("Статус подтверждён" if is_verified else "Верификация снята")
        + (f". {note}" if note else ""),
        payload={"is_verified": is_verified, "note": note},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


# --- Заявки на роль (поисковик / краевед) -----------------------------------


@router.get("/role-applications", summary="Заявки на роль поисковика/краеведа")
async def list_role_applications(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    application_status: Annotated[str | None, Query(alias="status")] = "pending",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params: dict = {"limit": limit, "offset": offset}
    if application_status:
        params["status"] = application_status
    return await upstream.call("user", "GET", "/internal/role-applications", params=params)


@router.post("/role-applications/{application_id}/approve", summary="Одобрить заявку на роль")
async def approve_role_application(
    application_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    note: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "user",
        "POST",
        f"/internal/role-applications/{application_id}/approve",
        actor_id=admin.id,
        json={"note": note},
    )
    audit.record(
        admin,
        action="role_application.approve",
        target_service="user_service",
        target_type="role_application",
        target_id=application_id,
        target_label=_label(result, "requested_role", fallback=application_id),
        message=f"Заявка на роль «{(result or {}).get('requested_role')}» одобрена. {note}".strip(),
        payload={"note": note},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.post("/role-applications/{application_id}/reject", summary="Отклонить заявку на роль")
async def reject_role_application(
    application_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    note: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "user",
        "POST",
        f"/internal/role-applications/{application_id}/reject",
        actor_id=admin.id,
        json={"note": note},
    )
    audit.record(
        admin,
        action="role_application.reject",
        target_service="user_service",
        target_type="role_application",
        target_id=application_id,
        target_label=_label(result, "requested_role", fallback=application_id),
        message=f"Заявка на роль «{(result or {}).get('requested_role')}» отклонена. {note}".strip(),
        payload={"note": note},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


# --- Модерация народного архива -------------------------------------------


@router.get("/entries", summary="Записи народного архива")
async def list_entries(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    entry_status: Annotated[str | None, Query(alias="status")] = None,
    kind: Annotated[str | None, Query()] = None,
    query: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if entry_status:
        params["status"] = entry_status
    if kind:
        params["kind"] = kind
    if query:
        params["query"] = query
    return await upstream.call("archive", "GET", "/internal/entries", params=params)


@router.post("/entries/{entry_id}/verify", summary="Подтвердить запись архива")
async def verify_entry(
    entry_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    note: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "archive",
        "POST",
        f"/internal/entries/{entry_id}/verify",
        actor_id=admin.id,
        json={"note": note},
    )
    audit.record(
        admin,
        action="entry.verify",
        target_service="archive_service",
        target_type="archive_entry",
        target_id=entry_id,
        target_label=_label(result, "title", fallback=entry_id),
        message=f"Запись подтверждена. {note}".strip(),
        payload={"note": note},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.post("/entries/{entry_id}/reject", summary="Отклонить запись архива")
async def reject_entry(
    entry_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    note: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "archive",
        "POST",
        f"/internal/entries/{entry_id}/reject",
        actor_id=admin.id,
        json={"note": note},
    )
    audit.record(
        admin,
        action="entry.reject",
        target_service="archive_service",
        target_type="archive_entry",
        target_id=entry_id,
        target_label=_label(result, "title", fallback=entry_id),
        message=f"Запись отклонена. {note}".strip(),
        payload={"note": note},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


# --- Точки «Последнего боя» ------------------------------------------------


@router.get("/last-stand", summary="Точки «Последнего боя»")
async def list_last_stand(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    point_status: Annotated[str | None, Query(alias="status")] = None,
    query: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if point_status:
        params["status"] = point_status
    if query:
        params["query"] = query
    return await upstream.call("map", "GET", "/internal/last-stand", params=params)


@router.patch("/last-stand/{point_id}/status", summary="Сменить статус точки")
async def set_last_stand_status(
    point_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    new_status: Annotated[str, Body(embed=True, alias="status")],
    reason: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "map",
        "PATCH",
        f"/internal/last-stand/{point_id}/status",
        actor_id=admin.id,
        # Основание идёт и в историю точки (map_service), а не только в наш
        # журнал: людям в приложении видно, почему стадия сменилась.
        json={"status": new_status, "note": reason},
    )
    audit.record(
        admin,
        action="last_stand.status.set",
        target_service="map_service",
        target_type="last_stand_point",
        target_id=point_id,
        target_label=_label(result, "soldier_name", "place", fallback=point_id),
        message=f"Статус точки → {new_status}" + (f". Основание: {reason}" if reason else ""),
        payload={"status": new_status, "reason": reason},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.delete(
    "/last-stand/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить точку",
)
async def delete_last_stand(
    point_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    # У DELETE тело передаётся не всеми клиентами — основание берём из query.
    reason: Annotated[str, Query(description="основание удаления")] = "",
) -> Response:
    await upstream.call(
        "map", "DELETE", f"/internal/last-stand/{point_id}", actor_id=admin.id
    )
    audit.record(
        admin,
        action="last_stand.delete",
        target_service="map_service",
        target_type="last_stand_point",
        target_id=point_id,
        target_label=point_id,
        message=f"Точка удалена. Основание: {reason}" if reason else "Точка удалена",
        payload={"reason": reason},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Поисковый штаб: отряды, сборы, выезды --------------------------------


@router.get("/squads", summary="Поисковые отряды")
async def list_squads(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    query: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if query:
        params["query"] = query
    return await upstream.call("search_hq", "GET", "/internal/squads", params=params)


@router.get("/needs", summary="Потребности и денежные сборы")
async def list_needs(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    need_status: Annotated[str | None, Query(alias="status")] = None,
    kind: Annotated[str | None, Query()] = None,
    squad_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if need_status:
        params["status"] = need_status
    if kind:
        params["kind"] = kind
    if squad_id:
        params["squad_id"] = squad_id
    return await upstream.call("search_hq", "GET", "/internal/needs", params=params)


@router.post("/needs/{need_id}/close", summary="Закрыть сбор или потребность")
async def close_need(
    need_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    reason: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "search_hq", "POST", f"/internal/needs/{need_id}/close", actor_id=admin.id
    )
    audit.record(
        admin,
        action="need.close",
        target_service="search_hq_service",
        target_type="squad_need",
        target_id=need_id,
        target_label=_label(result, "title", fallback=need_id),
        message=f"Сбор закрыт. {reason}".strip(),
        payload={"reason": reason},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.get("/trips", summary="Выезды «Выходные с поисковиком»")
async def list_trips(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    upcoming_only: Annotated[bool, Query()] = False,
    squad_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset, "upcoming_only": upcoming_only}
    if squad_id:
        params["squad_id"] = squad_id
    return await upstream.call("search_hq", "GET", "/internal/trips", params=params)


# --- Маршруты --------------------------------------------------------------


@router.get("/routes", summary="Маршруты, включая черновики")
async def list_routes(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    is_published: Annotated[bool | None, Query()] = None,
    mode: Annotated[str | None, Query()] = None,
    query: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if is_published is not None:
        params["is_published"] = is_published
    if mode:
        params["mode"] = mode
    if query:
        params["query"] = query
    return await upstream.call("route", "GET", "/internal/routes", params=params)


@router.post("/routes/{route_id}/publish", summary="Опубликовать или снять маршрут")
async def publish_route(
    route_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    is_published: Annotated[bool, Body(embed=True)] = True,
) -> dict:
    result = await upstream.call(
        "route",
        "POST",
        f"/internal/routes/{route_id}/publish",
        actor_id=admin.id,
        json={"is_published": is_published},
    )
    audit.record(
        admin,
        action="route.publish",
        target_service="route_service",
        target_type="route",
        target_id=route_id,
        target_label=_label(result, "title", fallback=route_id),
        message="Маршрут опубликован" if is_published else "Маршрут снят с публикации",
        payload={"is_published": is_published},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


# --- «Живое фото» ----------------------------------------------------------


@router.get("/clips", summary="Заявки на оживление фотографий")
async def list_clips(
    admin: AuthedAdmin,
    upstream: UpstreamDep,
    clip_status: Annotated[str | None, Query(alias="status")] = None,
    is_public: Annotated[bool | None, Query()] = None,
    query: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    params = {"limit": limit, "offset": offset}
    if clip_status:
        params["status"] = clip_status
    if is_public is not None:
        params["is_public"] = is_public
    if query:
        params["query"] = query
    return await upstream.call("media", "GET", "/internal/clips", params=params)


@router.post("/clips/{clip_id}/retry", summary="Перезапустить неудавшуюся генерацию")
async def retry_clip(
    clip_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
) -> dict:
    result = await upstream.call(
        "media", "POST", f"/internal/clips/{clip_id}/retry", actor_id=admin.id
    )
    audit.record(
        admin,
        action="clip.retry",
        target_service="media_service",
        target_type="memorial_clip",
        target_id=clip_id,
        target_label=_label(result, "soldier_name", fallback=clip_id),
        message="Генерация поставлена в очередь заново",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result


@router.patch("/clips/{clip_id}/visibility", summary="Снять клип с публикации или вернуть")
async def set_clip_visibility(
    clip_id: str,
    admin: WriteAdmin,
    upstream: UpstreamDep,
    audit: AuditServiceDep,
    client: Client,
    is_public: Annotated[bool, Body(embed=True)],
    reason: Annotated[str, Body(embed=True)] = "",
) -> dict:
    result = await upstream.call(
        "media",
        "PATCH",
        f"/internal/clips/{clip_id}",
        actor_id=admin.id,
        json={"is_public": is_public},
    )
    audit.record(
        admin,
        action="clip.visibility.set",
        target_service="media_service",
        target_type="memorial_clip",
        target_id=clip_id,
        target_label=_label(result, "soldier_name", fallback=clip_id),
        message=("Клип опубликован в мемориале" if is_public else "Клип снят с публикации")
        + (f". Основание: {reason}" if reason else ""),
        payload={"is_public": is_public, "reason": reason},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return result
