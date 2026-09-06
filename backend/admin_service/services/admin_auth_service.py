"""Аутентификация администратора: пароль → TOTP → пара токенов."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.orm import Session

from core import security
from core.config import settings
from core.exceptions import (
    AccountLocked,
    InactiveAdmin,
    InvalidCredentials,
    InvalidRefreshToken,
    InvalidToken,
    InvalidTotpCode,
    TotpAlreadyEnabled,
    TotpNotConfigured,
    WrongPassword,
)
from core.models import AdminUser
from repositories.admin_repository import AdminRepository
from repositories.session_repository import SessionRepository


@dataclass
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass
class LoginResult:
    """Либо пара токенов, либо требование второго фактора."""

    mfa_required: bool
    admin: AdminUser
    tokens: IssuedTokens | None = None
    mfa_token: str | None = None
    mfa_expires_in: int | None = None


@dataclass
class TotpSetup:
    secret: str
    otpauth_uri: str


def _aware(value: datetime | None) -> datetime | None:
    """sqlite отдаёт наивный datetime — приводим к UTC перед сравнением."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class AdminAuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.admins = AdminRepository(db)
        self.sessions = SessionRepository(db)

    # --- вход ----------------------------------------------------------

    def login(
        self, *, email: str, password: str, ip: str = "", user_agent: str = ""
    ) -> LoginResult:
        admin = self.admins.get_by_email(self._normalize_email(email))
        if admin is None:
            security.burn_time()  # не выдаём, существует ли учётка
            raise InvalidCredentials

        locked_until = _aware(admin.locked_until)
        if locked_until is not None and locked_until > datetime.now(UTC):
            minutes = max(1, int((locked_until - datetime.now(UTC)).total_seconds() // 60) + 1)
            raise AccountLocked(f"Вход заблокирован. Повторите через {minutes} мин.")

        if not security.verify_password(password, admin.password_hash):
            self._register_failed_attempt(admin)
            raise InvalidCredentials

        if not admin.is_active:
            raise InactiveAdmin

        # Успех: сбрасываем счётчик и обновляем хэш, если параметры argon2 сменились.
        admin.failed_attempts = 0
        admin.locked_until = None
        if security.password_needs_rehash(admin.password_hash):
            admin.password_hash = security.hash_password(password)

        if admin.totp_enabled:
            mfa_token, expires_in = security.create_mfa_token(admin.id)
            self.db.commit()
            return LoginResult(
                mfa_required=True,
                admin=admin,
                mfa_token=mfa_token,
                mfa_expires_in=expires_in,
            )

        tokens = self._issue(admin, mfa=False, ip=ip, user_agent=user_agent)
        self._mark_login(admin, ip)
        self.db.commit()
        return LoginResult(mfa_required=False, admin=admin, tokens=tokens)

    def complete_mfa(
        self, *, mfa_token: str, code: str, ip: str = "", user_agent: str = ""
    ) -> tuple[AdminUser, IssuedTokens]:
        try:
            payload = security.decode_token(mfa_token, expected_type=security.TOKEN_TYPE_MFA)
        except jwt.PyJWTError:
            raise InvalidToken("Сессия подтверждения истекла — войдите заново")

        admin = self.admins.get(payload["sub"])
        if admin is None or not admin.is_active:
            raise InvalidCredentials
        if not admin.totp_enabled or not admin.totp_secret:
            raise TotpNotConfigured

        if not self._consume_second_factor(admin, code):
            self._register_failed_attempt(admin)
            raise InvalidTotpCode

        admin.failed_attempts = 0
        admin.locked_until = None
        tokens = self._issue(admin, mfa=True, ip=ip, user_agent=user_agent)
        self._mark_login(admin, ip)
        self.db.commit()
        return admin, tokens

    # --- токены --------------------------------------------------------

    def refresh(
        self, raw_refresh_token: str, *, ip: str = "", user_agent: str = ""
    ) -> IssuedTokens:
        row = self.sessions.get_by_hash(security.hash_refresh_token(raw_refresh_token))
        if row is None:
            raise InvalidRefreshToken

        if not row.is_active:
            # Повторное использование отозванного токена — гасим все сессии.
            self.sessions.revoke_all_for(row.admin_id)
            self.db.commit()
            raise InvalidRefreshToken("Сессия скомпрометирована — войдите заново")

        admin = self.admins.get(row.admin_id)
        if admin is None or not admin.is_active:
            raise InvalidRefreshToken

        # Второй фактор уже был пройден в этой цепочке — сохраняем его в новом токене.
        mfa = admin.totp_enabled
        new_raw = security.generate_refresh_token()
        new_row = self.sessions.add(
            admin_id=admin.id,
            token_hash=security.hash_refresh_token(new_raw),
            expires_at=security.refresh_token_expiry(),
            ip=ip,
            user_agent=user_agent,
        )
        self.sessions.revoke(row, replaced_by=new_row.id)

        access, expires_in = security.create_access_token(
            admin_id=admin.id, email=admin.email, role=admin.role.value, mfa=mfa
        )
        self.db.commit()
        return IssuedTokens(access_token=access, refresh_token=new_raw, expires_in=expires_in)

    def logout(self, raw_refresh_token: str) -> None:
        row = self.sessions.get_by_hash(security.hash_refresh_token(raw_refresh_token))
        if row is not None and row.revoked_at is None:
            self.sessions.revoke(row)
            self.db.commit()

    def logout_everywhere(self, admin: AdminUser) -> int:
        count = self.sessions.revoke_all_for(admin.id)
        self.db.commit()
        return count

    # --- пароль --------------------------------------------------------

    def change_password(
        self, admin: AdminUser, *, current_password: str, new_password: str
    ) -> None:
        if not security.verify_password(current_password, admin.password_hash):
            raise WrongPassword
        admin.password_hash = security.hash_password(new_password)
        self.sessions.revoke_all_for(admin.id)  # разлогинить все устройства
        self.db.commit()

    # --- TOTP ----------------------------------------------------------

    def start_totp_setup(self, admin: AdminUser) -> TotpSetup:
        if admin.totp_enabled:
            raise TotpAlreadyEnabled
        secret = security.generate_totp_secret()
        admin.totp_secret = secret  # ещё не включён — до confirm вход по нему не требуется
        self.db.commit()
        return TotpSetup(
            secret=secret, otpauth_uri=security.totp_provisioning_uri(secret, admin.email)
        )

    def confirm_totp(self, admin: AdminUser, code: str) -> list[str]:
        """Включает 2FA и возвращает коды восстановления (показать один раз)."""
        if admin.totp_enabled:
            raise TotpAlreadyEnabled
        if not admin.totp_secret:
            raise TotpNotConfigured("Сначала выполните /auth/totp/setup")
        if not security.verify_totp(admin.totp_secret, code):
            raise InvalidTotpCode

        admin.totp_enabled = True
        admin.totp_confirmed_at = datetime.now(UTC)
        codes = self._regenerate_recovery_codes(admin)
        self.db.commit()
        return codes

    def disable_totp(self, admin: AdminUser, *, password: str, code: str) -> None:
        if not admin.totp_enabled:
            raise TotpNotConfigured
        if not security.verify_password(password, admin.password_hash):
            raise WrongPassword
        if not self._consume_second_factor(admin, code):
            raise InvalidTotpCode

        admin.totp_enabled = False
        admin.totp_secret = None
        admin.totp_confirmed_at = None
        self.admins.replace_recovery_codes(admin.id, [])
        self.sessions.revoke_all_for(admin.id)
        self.db.commit()

    def regenerate_recovery_codes(self, admin: AdminUser, *, code: str) -> list[str]:
        if not admin.totp_enabled:
            raise TotpNotConfigured
        if not security.verify_totp(admin.totp_secret or "", code):
            raise InvalidTotpCode
        codes = self._regenerate_recovery_codes(admin)
        self.db.commit()
        return codes

    def unused_recovery_codes(self, admin: AdminUser) -> int:
        return self.admins.count_unused_recovery_codes(admin.id)

    # --- helpers -------------------------------------------------------

    def _issue(
        self, admin: AdminUser, *, mfa: bool, ip: str, user_agent: str
    ) -> IssuedTokens:
        access, expires_in = security.create_access_token(
            admin_id=admin.id, email=admin.email, role=admin.role.value, mfa=mfa
        )
        raw_refresh = security.generate_refresh_token()
        self.sessions.add(
            admin_id=admin.id,
            token_hash=security.hash_refresh_token(raw_refresh),
            expires_at=security.refresh_token_expiry(),
            ip=ip,
            user_agent=user_agent,
        )
        return IssuedTokens(
            access_token=access, refresh_token=raw_refresh, expires_in=expires_in
        )

    def _consume_second_factor(self, admin: AdminUser, code: str) -> bool:
        """Принимает либо код из приложения, либо одноразовый код восстановления."""
        if security.verify_totp(admin.totp_secret or "", code):
            return True
        recovery = self.admins.get_unused_recovery_code(
            admin.id, security.hash_recovery_code(code)
        )
        if recovery is not None:
            recovery.used_at = datetime.now(UTC)
            return True
        return False

    def _regenerate_recovery_codes(self, admin: AdminUser) -> list[str]:
        codes = security.generate_recovery_codes(settings.recovery_codes_count)
        self.admins.replace_recovery_codes(
            admin.id, [security.hash_recovery_code(c) for c in codes]
        )
        return codes

    def _register_failed_attempt(self, admin: AdminUser) -> None:
        admin.failed_attempts += 1
        if admin.failed_attempts >= settings.max_failed_attempts:
            admin.locked_until = datetime.now(UTC) + timedelta(minutes=settings.lockout_minutes)
            admin.failed_attempts = 0
        self.db.commit()

    def _mark_login(self, admin: AdminUser, ip: str) -> None:
        admin.last_login_at = datetime.now(UTC)
        admin.last_login_ip = ip[:64]

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()
