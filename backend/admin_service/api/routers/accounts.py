"""Учётные записи администраторов. Доступно только superadmin."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from api.deps import AccountServiceDep, AuditServiceDep, Client, SuperAdmin
from api.schemas.account import ActiveUpdate, AdminCreate, AdminUpdate, PasswordReset
from api.schemas.auth import AdminOut
from core.models import AdminRole

router = APIRouter(prefix="/admin/accounts", tags=["admin: учётки администраторов"])


@router.get("", summary="Список администраторов")
def list_accounts(
    admin: SuperAdmin,
    service: AccountServiceDep,
    query: Annotated[str | None, Query(description="поиск по email или имени")] = None,
    role: Annotated[AdminRole | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    rows, total = service.search(
        query=query, role=role, is_active=is_active, limit=limit, offset=offset
    )
    return {
        "items": [AdminOut.model_validate(a) for a in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AdminCreate,
    admin: SuperAdmin,
    service: AccountServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> AdminOut:
    created = service.create(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
    )
    audit.record(
        admin,
        action="admin.account.create",
        target_type="admin_user",
        target_id=created.id,
        target_label=created.email,
        message=f"Создана учётка с ролью {created.role.value}",
        payload={"role": created.role.value},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return AdminOut.model_validate(created)


@router.get("/{admin_id}", response_model=AdminOut)
def get_account(admin_id: str, admin: SuperAdmin, service: AccountServiceDep) -> AdminOut:
    return AdminOut.model_validate(service.get(admin_id))


@router.patch("/{admin_id}", response_model=AdminOut)
def update_account(
    admin_id: str,
    payload: AdminUpdate,
    admin: SuperAdmin,
    service: AccountServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> AdminOut:
    before = service.get(admin_id)
    before_role = before.role.value
    updated = service.update(admin_id, payload.to_update_dict())
    audit.record(
        admin,
        action="admin.account.update",
        target_type="admin_user",
        target_id=updated.id,
        target_label=updated.email,
        message=f"Роль: {before_role} → {updated.role.value}",
        payload={"before": {"role": before_role}, "after": {"role": updated.role.value}},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return AdminOut.model_validate(updated)


@router.patch("/{admin_id}/active", response_model=AdminOut)
def set_active(
    admin_id: str,
    payload: ActiveUpdate,
    admin: SuperAdmin,
    service: AccountServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> AdminOut:
    updated = service.set_active(admin, admin_id, payload.is_active)
    audit.record(
        admin,
        action="admin.account.active",
        target_type="admin_user",
        target_id=updated.id,
        target_label=updated.email,
        message="Учётка включена" if payload.is_active else "Учётка отключена",
        payload={"is_active": payload.is_active},
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return AdminOut.model_validate(updated)


@router.post("/{admin_id}/reset-password", response_model=AdminOut)
def reset_password(
    admin_id: str,
    payload: PasswordReset,
    admin: SuperAdmin,
    service: AccountServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> AdminOut:
    updated = service.reset_password(admin_id, payload.new_password)
    audit.record(
        admin,
        action="admin.account.reset_password",
        target_type="admin_user",
        target_id=updated.id,
        target_label=updated.email,
        message="Пароль сброшен, сессии завершены",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return AdminOut.model_validate(updated)


@router.post(
    "/{admin_id}/reset-totp",
    response_model=AdminOut,
    summary="Снять 2FA (потерян телефон и коды восстановления)",
)
def reset_totp(
    admin_id: str,
    admin: SuperAdmin,
    service: AccountServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> AdminOut:
    updated = service.reset_totp(admin_id)
    audit.record(
        admin,
        action="admin.account.reset_totp",
        target_type="admin_user",
        target_id=updated.id,
        target_label=updated.email,
        message="Двухфакторная аутентификация снята администратором",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return AdminOut.model_validate(updated)


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    admin_id: str,
    admin: SuperAdmin,
    service: AccountServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> Response:
    target = service.get(admin_id)
    email = target.email
    service.delete(admin, admin_id)
    audit.record(
        admin,
        action="admin.account.delete",
        target_type="admin_user",
        target_id=admin_id,
        target_label=email,
        message="Учётка администратора удалена",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
