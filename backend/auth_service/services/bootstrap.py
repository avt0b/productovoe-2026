from core.config import settings
from core.db import SessionLocal
from core.models import Role
from repositories.user_repository import UserRepository
from services.auth_service import AuthService


def ensure_root_user() -> None:
    """Создаёт первого администратора (is_root=True), если задан в настройках."""
    if not (settings.bootstrap_root_email and settings.bootstrap_root_password):
        return

    email = settings.bootstrap_root_email.strip().lower()
    with SessionLocal() as db:
        users = UserRepository(db)
        existing = users.get_by_email(email)
        if existing is not None:
            if not existing.is_root:
                existing.is_root = True
                db.commit()
            return

        auth = AuthService(db)
        user = auth.register(
            email=email, password=settings.bootstrap_root_password, role=Role.moderator
        )
        user.is_root = True
        db.commit()
