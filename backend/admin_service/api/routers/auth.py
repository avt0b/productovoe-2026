"""Вход в админку: пароль → TOTP → пара токенов. Плюс управление 2FA."""

from datetime import UTC, datetime

from fastapi import APIRouter, Response, status

from api.deps import (
    AuditServiceDep,
    AuthServiceDep,
    Client,
    CurrentAdmin,
    TokenPayload,
)
from api.schemas.auth import (
    AdminOut,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MfaRequest,
    PasswordChange,
    RecoveryCodesResponse,
    RefreshRequest,
    TokenPair,
    TotpConfirmRequest,
    TotpDisableRequest,
    TotpSetupResponse,
)
from core.config import settings

router = APIRouter(prefix="/admin/auth", tags=["admin: аутентификация"])


@router.post("/login", response_model=LoginResponse, summary="Шаг 1 — email и пароль")
def login(
    payload: LoginRequest,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> LoginResponse:
    result = service.login(
        email=payload.email,
        password=payload.password,
        ip=client.ip,
        user_agent=client.user_agent,
    )

    if result.mfa_required:
        return LoginResponse(
            mfa_required=True,
            mfa_token=result.mfa_token,
            mfa_expires_in=result.mfa_expires_in,
        )

    audit.record(
        result.admin,
        action="admin.login",
        message="Вход без второго фактора",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    tokens = result.tokens
    return LoginResponse(
        mfa_required=False,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post(
    "/login/mfa",
    response_model=TokenPair,
    summary="Шаг 2 — код из приложения или код восстановления",
)
def login_mfa(
    payload: MfaRequest,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> TokenPair:
    admin, tokens = service.complete_mfa(
        mfa_token=payload.mfa_token,
        code=payload.code,
        ip=client.ip,
        user_agent=client.user_agent,
    )
    audit.record(
        admin,
        action="admin.login",
        message="Вход подтверждён вторым фактором",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return TokenPair(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/refresh", response_model=TokenPair, summary="Ротация пары токенов")
def refresh(payload: RefreshRequest, service: AuthServiceDep, client: Client) -> TokenPair:
    tokens = service.refresh(
        payload.refresh_token, ip=client.ip, user_agent=client.user_agent
    )
    return TokenPair(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Выход")
def logout(payload: RefreshRequest, service: AuthServiceDep) -> Response:
    service.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/logout-everywhere",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Завершить все сессии администратора",
)
def logout_everywhere(
    admin: CurrentAdmin,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> Response:
    count = service.logout_everywhere(admin)
    audit.record(
        admin,
        action="admin.logout_all",
        message=f"Завершено сессий: {count}",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse, summary="Текущий администратор")
def me(admin: CurrentAdmin, payload: TokenPayload, service: AuthServiceDep) -> MeResponse:
    return MeResponse(
        **AdminOut.model_validate(admin).model_dump(),
        mfa_satisfied="otp" in payload.get("amr", []),
        totp_required_by_policy=settings.require_totp,
        unused_recovery_codes=service.unused_recovery_codes(admin),
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Смена пароля (гасит все сессии)",
)
def change_password(
    payload: PasswordChange,
    admin: CurrentAdmin,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> Response:
    service.change_password(
        admin,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    audit.record(
        admin,
        action="admin.password.change",
        message="Пароль изменён, все сессии завершены",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- TOTP ------------------------------------------------------------------


@router.post(
    "/totp/setup",
    response_model=TotpSetupResponse,
    summary="Выдать секрет и otpauth-ссылку (2FA ещё не включена)",
)
def totp_setup(admin: CurrentAdmin, service: AuthServiceDep) -> TotpSetupResponse:
    setup = service.start_totp_setup(admin)
    return TotpSetupResponse(secret=setup.secret, otpauth_uri=setup.otpauth_uri)


@router.post(
    "/totp/confirm",
    response_model=RecoveryCodesResponse,
    summary="Подтвердить код и включить 2FA — возвращает коды восстановления",
)
def totp_confirm(
    payload: TotpConfirmRequest,
    admin: CurrentAdmin,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> RecoveryCodesResponse:
    codes = service.confirm_totp(admin, payload.code)
    audit.record(
        admin,
        action="admin.totp.enable",
        message="Двухфакторная аутентификация включена",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return RecoveryCodesResponse(codes=codes, generated_at=datetime.now(UTC))


@router.post(
    "/totp/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отключить 2FA (нужны пароль и код)",
)
def totp_disable(
    payload: TotpDisableRequest,
    admin: CurrentAdmin,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> Response:
    service.disable_totp(admin, password=payload.password, code=payload.code)
    audit.record(
        admin,
        action="admin.totp.disable",
        message="Двухфакторная аутентификация отключена",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/totp/recovery-codes",
    response_model=RecoveryCodesResponse,
    summary="Перевыпустить коды восстановления (старые перестают действовать)",
)
def regenerate_recovery_codes(
    payload: TotpConfirmRequest,
    admin: CurrentAdmin,
    service: AuthServiceDep,
    audit: AuditServiceDep,
    client: Client,
) -> RecoveryCodesResponse:
    codes = service.regenerate_recovery_codes(admin, code=payload.code)
    audit.record(
        admin,
        action="admin.totp.recovery_codes",
        message="Коды восстановления перевыпущены",
        ip=client.ip,
        user_agent=client.user_agent,
    )
    return RecoveryCodesResponse(codes=codes, generated_at=datetime.now(UTC))
