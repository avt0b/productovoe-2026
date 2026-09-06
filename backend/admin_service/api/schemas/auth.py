from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from core.models import AdminRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MfaRequest(BaseModel):
    mfa_token: str
    # Либо 6 цифр из приложения, либо код восстановления вида ABCD-EF23.
    code: str = Field(min_length=4, max_length=32)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    """Один ответ на оба исхода входа.

    `mfa_required=true` → пришёл только `mfa_token`, его нужно обменять
    на пару токенов в `/admin/auth/login/mfa`.
    """

    mfa_required: bool
    mfa_token: str | None = None
    mfa_expires_in: int | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: AdminRole
    is_active: bool
    totp_enabled: bool
    last_login_at: datetime | None
    created_at: datetime


class MeResponse(AdminOut):
    # Насколько «полон» текущий вход — фронт по этому решает, вести ли
    # администратора на экран настройки 2FA.
    mfa_satisfied: bool
    totp_required_by_policy: bool
    unused_recovery_codes: int


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class TotpSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str  # фронт рисует из неё QR-код


class TotpConfirmRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TotpDisableRequest(BaseModel):
    password: str
    code: str = Field(min_length=4, max_length=32)


class RecoveryCodesResponse(BaseModel):
    """Коды показываются ровно один раз — повторно их не получить."""

    codes: list[str]
    generated_at: datetime
