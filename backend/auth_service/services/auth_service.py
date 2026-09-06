from dataclasses import dataclass

from sqlalchemy.orm import Session

from core import security
from core.exceptions import (
    EmailAlreadyExists,
    InactiveUser,
    InvalidCredentials,
    InvalidRefreshToken,
    WrongPassword,
)
from core.models import Role, User
from repositories.refresh_token_repository import RefreshTokenRepository
from repositories.user_repository import UserRepository


@dataclass
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    """Слой бизнес-логики аутентификации. Оркеструет репозитории и транзакцию."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    # --- регистрация / вход ---------------------------------------------

    def register(self, *, email: str, password: str, role: Role) -> User:
        email = self._normalize_email(email)
        if self.users.exists_by_email(email):
            raise EmailAlreadyExists
        user = self.users.create(
            email=email, password_hash=security.hash_password(password), role=role
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, *, email: str, password: str) -> User:
        user = self.users.get_by_email(self._normalize_email(email))
        if user is None or not security.verify_password(password, user.password_hash):
            raise InvalidCredentials
        if not user.is_active:
            raise InactiveUser

        if security.password_needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(password)
            self.db.commit()
        return user

    def login(self, *, email: str, password: str) -> IssuedTokens:
        user = self.authenticate(email=email, password=password)
        return self.issue_tokens(user)

    # --- токены --------------------------------------------------------

    def issue_tokens(self, user: User) -> IssuedTokens:
        access, expires_in = security.create_access_token(
            user_id=user.id, role=user.role.value, is_root=user.is_root
        )
        raw_refresh = self._store_refresh_token(user.id)
        self.db.commit()
        return IssuedTokens(access_token=access, refresh_token=raw_refresh, expires_in=expires_in)

    def refresh(self, raw_refresh_token: str) -> IssuedTokens:
        row = self.refresh_tokens.get_by_hash(security.hash_refresh_token(raw_refresh_token))
        if row is None:
            raise InvalidRefreshToken

        if not row.is_active:
            # Переиспользование отозванного/истёкшего токена => компрометация цепочки.
            self.refresh_tokens.revoke_all_for_user(row.user_id)
            self.db.commit()
            raise InvalidRefreshToken

        user = self.users.get(row.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshToken

        new_raw = self._store_refresh_token(user.id)
        new_row = self.refresh_tokens.get_by_hash(security.hash_refresh_token(new_raw))
        self.refresh_tokens.revoke(row, replaced_by=new_row.id if new_row else None)

        access, expires_in = security.create_access_token(
            user_id=user.id, role=user.role.value, is_root=user.is_root
        )
        self.db.commit()
        return IssuedTokens(access_token=access, refresh_token=new_raw, expires_in=expires_in)

    def logout(self, raw_refresh_token: str) -> None:
        row = self.refresh_tokens.get_by_hash(security.hash_refresh_token(raw_refresh_token))
        if row is not None and row.revoked_at is None:
            self.refresh_tokens.revoke(row)
            self.db.commit()

    # --- пароль -------------------------------------------------------

    def change_password(self, user: User, *, current_password: str, new_password: str) -> None:
        if not security.verify_password(current_password, user.password_hash):
            raise WrongPassword
        user.password_hash = security.hash_password(new_password)
        self.refresh_tokens.revoke_all_for_user(user.id)  # разлогинить все сессии
        self.db.commit()

    # --- helpers -----------------------------------------------------

    def _store_refresh_token(self, user_id: str) -> str:
        raw = security.generate_refresh_token()
        self.refresh_tokens.add(
            user_id=user_id,
            token_hash=security.hash_refresh_token(raw),
            expires_at=security.refresh_token_expiry(),
        )
        return raw

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()
