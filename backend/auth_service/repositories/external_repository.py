from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import ExternalIdentity, ExternalLogin, ExternalProvider


class ExternalRepository:
    """Доступ к таблицам внешнего входа: попытки входа и привязанные аккаунты."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- попытки входа ---

    def add_login(self, login: ExternalLogin) -> ExternalLogin:
        self.db.add(login)
        self.db.flush()
        return login

    def login_by_hash(self, login_hash: str) -> ExternalLogin | None:
        return self.db.scalar(select(ExternalLogin).where(ExternalLogin.login_hash == login_hash))

    def login_by_state(self, provider: ExternalProvider, state: str) -> ExternalLogin | None:
        return self.db.scalar(
            select(ExternalLogin).where(
                ExternalLogin.provider == provider, ExternalLogin.state == state
            )
        )

    # --- привязанные аккаунты ---

    def identity(self, provider: ExternalProvider, subject: str) -> ExternalIdentity | None:
        return self.db.scalar(
            select(ExternalIdentity).where(
                ExternalIdentity.provider == provider, ExternalIdentity.subject == subject
            )
        )

    def add_identity(self, identity: ExternalIdentity) -> ExternalIdentity:
        self.db.add(identity)
        self.db.flush()
        return identity
