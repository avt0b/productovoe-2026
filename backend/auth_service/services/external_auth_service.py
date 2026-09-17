import base64
import hashlib
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from core import security
from core.config import settings
from core.exceptions import (
    ExternalLoginExpired,
    ExternalLoginFailed,
    ExternalLoginNotFound,
    ExternalProviderError,
    ExternalProviderNotConfigured,
    InactiveUser,
    InvalidExternalResultCode,
    InvalidReturnUrl,
    PermissionDenied,
)
from core.models import (
    ExternalIdentity,
    ExternalLogin,
    ExternalLoginStatus,
    ExternalProvider,
    Role,
    User,
)
from repositories.external_repository import ExternalRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService, IssuedTokens
from services.external.base import AuthorizeRequest, ExternalProfile, ProviderClient, ProviderKind
from services.external.registry import get_provider


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    # SQLite (тесты) отдаёт даты без пояса, Postgres — с поясом.
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@dataclass(frozen=True)
class ProviderInfo:
    provider: ExternalProvider
    title: str
    enabled: bool
    kind: ProviderKind
    mock: bool


@dataclass(frozen=True)
class StartedLogin:
    login_id: str
    provider: ExternalProvider
    authorize_url: str
    kind: ProviderKind
    expires_in: int


@dataclass(frozen=True)
class CompletedLogin:
    tokens: IssuedTokens
    user: User
    display_name: str
    is_new_user: bool


class ExternalAuthService:
    """Вход через VK ID, MAX и Госуслуги.

    1. Приложение начинает попытку (`start`) и получает login_id — секрет попытки —
       и ссылку, куда отправить человека.
    2. Человек подтверждает вход у провайдера: redirect-провайдер возвращает его на
       callback, бот MAX присылает webhook.
    3. Приложение забирает токены (`complete`) по login_id. После redirect ещё нужен
       одноразовый result_code: он приходит только на устройство, где человек
       подтвердил вход, поэтому чужая ссылка входа не отдаёт токены тому, кто её прислал.

    Токены никогда не попадают в URL.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExternalRepository(db)
        self.users = UserRepository(db)
        self.auth = AuthService(db)

    # --- какие способы входа есть ---

    def providers(self) -> list[ProviderInfo]:
        infos = []
        for provider in ExternalProvider:
            client = get_provider(provider)
            infos.append(
                ProviderInfo(
                    provider=provider,
                    title=client.title,
                    enabled=client.is_enabled(),
                    kind=client.kind,
                    mock=client.mock,
                )
            )
        return infos

    # --- 1. начать вход ---

    def start(self, provider: ExternalProvider, return_to: str | None) -> StartedLogin:
        client = get_provider(provider)
        if not client.is_enabled():
            raise ExternalProviderNotConfigured(client.disabled_reason())

        return_to = (return_to or "").strip()
        if return_to and not self._return_allowed(return_to):
            raise InvalidReturnUrl
        if client.kind == "redirect" and not return_to:
            raise InvalidReturnUrl(
                f"Для входа через {client.title} нужен return_to — адрес возврата в приложение"
            )

        login_id = secrets.token_urlsafe(32)
        state = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(48) if client.kind == "redirect" else ""
        ttl = settings.external_auth_login_ttl_seconds

        self.repo.add_login(
            ExternalLogin(
                provider=provider,
                login_hash=_hash(login_id),
                state=state,
                code_verifier=verifier,
                return_to=return_to,
                status=ExternalLoginStatus.pending,
                expires_at=_utcnow() + timedelta(seconds=ttl),
            )
        )
        authorize_url = client.authorize_url(
            AuthorizeRequest(
                state=state,
                code_challenge=_code_challenge(verifier) if verifier else "",
                redirect_uri=self.callback_url(provider),
            )
        )
        self.db.commit()
        return StartedLogin(
            login_id=login_id,
            provider=provider,
            authorize_url=authorize_url,
            kind=client.kind,
            expires_in=ttl,
        )

    @staticmethod
    def callback_url(provider: ExternalProvider) -> str:
        base = settings.external_auth_public_url.rstrip("/")
        return f"{base}/auth/external/{provider.value}/callback"

    # --- 2а. redirect-провайдер вернул человека ---

    def handle_callback(self, provider: ExternalProvider, params: Mapping[str, str]) -> str:
        """Разобрать возврат от провайдера. Возвращает адрес, куда отправить человека дальше."""
        state = params.get("state") or ""
        login = self.repo.login_by_state(provider, state) if state else None
        if login is None or login.status is not ExternalLoginStatus.pending:
            raise ExternalLoginNotFound
        if self._expired(login):
            raise ExternalLoginExpired

        if params.get("error"):
            reason = params.get("error_description") or "человек отказался от входа"
            return self._fail(login, f"Вход не подтверждён: {reason}")

        code = params.get("code") or ""
        if not code:
            return self._fail(login, "Провайдер не вернул код входа")

        client = get_provider(provider)
        try:
            profile = client.exchange(
                code=code,
                code_verifier=login.code_verifier,
                redirect_uri=self.callback_url(provider),
                state=state,
                params=params,
            )
        except ExternalProviderError as error:
            return self._fail(login, error.detail)

        result_code = secrets.token_urlsafe(32)
        self._confirm(login, provider, profile)
        login.result_code_hash = _hash(result_code)
        self.db.commit()
        return self._return_location(login, {"result_code": result_code})

    # --- 2б. бот MAX прислал обновление ---

    def handle_bot_update(
        self, provider: ExternalProvider, secret: str | None, update: Mapping[str, Any]
    ) -> bool:
        """Подтвердить попытку по webhook бота. `False` — обновление не про вход, пропускаем."""
        client: ProviderClient = get_provider(provider)
        if client.kind != "bot" or not client.verify_webhook(secret):
            raise PermissionDenied("Webhook бота не прошёл проверку")

        parsed = client.parse_webhook(update)
        if parsed is None:
            return False
        state, profile = parsed
        login = self.repo.login_by_state(provider, state)
        if login is None or login.status is not ExternalLoginStatus.pending or self._expired(login):
            return False

        self._confirm(login, provider, profile)
        self.db.commit()
        return True

    # --- 3. забрать токены ---

    def complete(self, login_id: str, result_code: str | None) -> CompletedLogin | None:
        """Токены по подтверждённой попытке. `None` — человек ещё не подтвердил вход."""
        login = self.repo.login_by_hash(_hash(login_id))
        if login is None:
            raise ExternalLoginNotFound
        if login.status is ExternalLoginStatus.consumed:
            raise ExternalLoginExpired("Вход уже завершён — начните новый")
        if login.status is ExternalLoginStatus.failed:
            raise ExternalLoginFailed(login.error or None)
        if self._expired(login):
            raise ExternalLoginExpired
        if login.status is ExternalLoginStatus.pending:
            return None

        if login.result_code_hash is not None and not (
            result_code and secrets.compare_digest(_hash(result_code), login.result_code_hash)
        ):
            raise InvalidExternalResultCode

        user = self.users.get(login.user_id) if login.user_id else None
        if user is None or not user.is_active:
            raise InactiveUser

        login.status = ExternalLoginStatus.consumed
        tokens = self.auth.issue_tokens(user)
        return CompletedLogin(
            tokens=tokens,
            user=user,
            display_name=login.display_name,
            is_new_user=login.is_new_user,
        )

    # --- helpers ---

    def _confirm(self, login: ExternalLogin, provider: ExternalProvider, profile: ExternalProfile) -> None:
        user, is_new = self._user_for(provider, profile)
        login.status = ExternalLoginStatus.completed
        login.user_id = user.id
        login.is_new_user = is_new
        login.display_name = profile.display_name

    def _user_for(self, provider: ExternalProvider, profile: ExternalProfile) -> tuple[User, bool]:
        """Пользователь, привязанный к аккаунту провайдера. Нет такого — новый, с ролью «семья»."""
        now = _utcnow()
        identity = self.repo.identity(provider, profile.subject)
        if identity is not None:
            identity.last_login_at = now
            if profile.display_name:
                identity.display_name = profile.display_name
            user = self.users.get(identity.user_id)
            if user is None or not user.is_active:
                raise InactiveUser
            return user, False

        # Почта у пользователя обязательна (на неё завязаны вход по паролю, админка,
        # приложение), поэтому — служебный адрес на нашем домене. Пароль случайный и
        # никому не известен: войти можно только через этого провайдера.
        user = self.users.create(
            email=self._service_email(provider, profile.subject),
            password_hash=security.hash_password(secrets.token_urlsafe(32)),
            role=Role.family,
        )
        self.repo.add_identity(
            ExternalIdentity(
                user_id=user.id,
                provider=provider,
                subject=profile.subject,
                display_name=profile.display_name,
                email=profile.email,
                last_login_at=now,
            )
        )
        return user, True

    def _service_email(self, provider: ExternalProvider, subject: str) -> str:
        local = re.sub(r"[^a-z0-9._-]", "", subject.lower())[:48] or secrets.token_hex(6)
        email = f"{provider.value}-{local}@{settings.external_auth_email_domain}"
        if self.users.exists_by_email(email):
            email = f"{provider.value}-{local}-{secrets.token_hex(4)}@{settings.external_auth_email_domain}"
        return email

    def _fail(self, login: ExternalLogin, reason: str) -> str:
        login.status = ExternalLoginStatus.failed
        login.error = reason
        self.db.commit()
        return self._return_location(login, {"error": reason})

    @staticmethod
    def _return_location(login: ExternalLogin, extra: dict[str, str]) -> str:
        query = urlencode({"provider": login.provider.value, **extra})
        separator = "&" if "?" in login.return_to else "?"
        return f"{login.return_to}{separator}{query}"

    @staticmethod
    def _expired(login: ExternalLogin) -> bool:
        return _as_utc(login.expires_at) <= _utcnow()

    @staticmethod
    def _return_allowed(url: str) -> bool:
        """Вернуть человека можно только в приложение: иначе ручка стала бы открытым редиректом.

        Совпадение по началу адреса — с границей: `https://localhost` не пускает
        `https://localhost.evil.example`.
        """
        for prefix in settings.external_auth_return_prefixes:
            if prefix.endswith(("/", ":")):
                if url.startswith(prefix):
                    return True
            elif url == prefix or url.startswith((prefix + "/", prefix + "?", prefix + "#")):
                return True
        return False
