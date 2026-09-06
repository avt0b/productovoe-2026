from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.models import Role, User


class UserRepository:
    """Доступ к таблице users. Только БД, без бизнес-логики."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def exists_by_email(self, email: str) -> bool:
        return self.db.scalar(select(User.id).where(User.email == email)) is not None

    def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[User]:
        return self.db.scalars(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        ).all()

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def create(self, *, email: str, password_hash: str, role: Role) -> User:
        return self.add(
            User(email=email, password_hash=password_hash, role=role, is_root=False)
        )
