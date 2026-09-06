from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import UserNotFound
from core.models import Role, User
from repositories.refresh_token_repository import RefreshTokenRepository
from repositories.user_repository import UserRepository


class UserAdminService:
    """Управление пользователями из админки (доступно только is_root)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def list_users(self, *, limit: int = 50, offset: int = 0) -> Sequence[User]:
        return self.users.list(limit=limit, offset=offset)

    def get_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise UserNotFound
        return user

    def set_role(self, user_id: str, role: Role) -> User:
        user = self.get_user(user_id)
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_active(self, user_id: str, is_active: bool) -> User:
        user = self.get_user(user_id)
        user.is_active = is_active
        if not is_active:
            self.refresh_tokens.revoke_all_for_user(user.id)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_root(self, user_id: str, is_root: bool) -> User:
        user = self.get_user(user_id)
        user.is_root = is_root
        self.db.commit()
        self.db.refresh(user)
        return user
