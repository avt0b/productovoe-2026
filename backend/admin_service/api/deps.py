from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core import security
from core.config import settings
from core.db import get_db
from core.models import WRITE_ROLES, AdminRole, AdminUser
from repositories.admin_repository import AdminRepository
from services.account_service import AccountService
from services.admin_auth_service import AdminAuthService
from services.audit_service import AuditService
from services.dashboard_service import DashboardService
from services.upstream import Upstream

_bearer = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_db)]


# --- контекст запроса ------------------------------------------------------


@dataclass(frozen=True)
class ClientMeta:
    """IP и User-Agent — попадают в сессию и в журнал аудита."""

    ip: str
    user_agent: str


def get_client_meta(request: Request) -> ClientMeta:
    # X-Forwarded-For заполняет reverse proxy; берём первый адрес цепочки.
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else ""
    )
    return ClientMeta(ip=ip[:64], user_agent=request.headers.get("User-Agent", "")[:400])


Client = Annotated[ClientMeta, Depends(get_client_meta)]


# --- сервисы ---------------------------------------------------------------


def get_auth_service(db: DbSession) -> AdminAuthService:
    return AdminAuthService(db)


def get_account_service(db: DbSession) -> AccountService:
    return AccountService(db)


def get_audit_service(db: DbSession) -> AuditService:
    return AuditService(db)


def get_upstream(request: Request) -> Upstream:
    return request.app.state.upstream


def get_dashboard_service(upstream: Annotated[Upstream, Depends(get_upstream)]) -> DashboardService:
    return DashboardService(upstream)


AuthServiceDep = Annotated[AdminAuthService, Depends(get_auth_service)]
AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
AuditServiceDep = Annotated[AuditService, Depends(get_audit_service)]
UpstreamDep = Annotated[Upstream, Depends(get_upstream)]
DashboardServiceDep = Annotated[DashboardService, Depends(get_dashboard_service)]


# --- аутентификация --------------------------------------------------------

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Недействительный токен администратора",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_token_payload(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict:
    try:
        return security.decode_token(
            creds.credentials, expected_type=security.TOKEN_TYPE_ACCESS
        )
    except jwt.PyJWTError:
        raise _CREDENTIALS_ERROR


TokenPayload = Annotated[dict, Depends(get_token_payload)]


def get_current_admin(payload: TokenPayload, db: DbSession) -> AdminUser:
    admin = AdminRepository(db).get(payload.get("sub", ""))
    if admin is None or not admin.is_active:
        raise _CREDENTIALS_ERROR
    return admin


CurrentAdmin = Annotated[AdminUser, Depends(get_current_admin)]


def require_mfa(admin: CurrentAdmin, payload: TokenPayload) -> AdminUser:
    """Пускает дальше только полностью аутентифицированного администратора.

    При `REQUIRE_TOTP=true` учётка без настроенного TOTP может дойти только
    до `/admin/auth/*` — то есть ровно до настройки второго фактора.
    """
    if settings.require_totp and not admin.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Настройте двухфакторную аутентификацию: POST /admin/auth/totp/setup",
        )
    if admin.totp_enabled and "otp" not in payload.get("amr", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется подтверждение кодом из приложения",
        )
    return admin


AuthedAdmin = Annotated[AdminUser, Depends(require_mfa)]


def require_roles(*roles: AdminRole):
    allowed = set(roles)

    def _dep(admin: AuthedAdmin) -> AdminUser:
        if admin.role is AdminRole.superadmin or admin.role in allowed:
            return admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для этого действия",
        )

    return _dep


def require_write(admin: AuthedAdmin) -> AdminUser:
    """Любое изменяющее действие: viewer только смотрит."""
    if admin.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Роль «наблюдатель» не может изменять данные",
        )
    return admin


def require_superadmin(admin: AuthedAdmin) -> AdminUser:
    if admin.role is not AdminRole.superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права суперадминистратора",
        )
    return admin


WriteAdmin = Annotated[AdminUser, Depends(require_write)]
SuperAdmin = Annotated[AdminUser, Depends(require_superadmin)]
