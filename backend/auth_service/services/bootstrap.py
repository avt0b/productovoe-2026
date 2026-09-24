from sqlalchemy import text

from core.config import settings
from core.db import SessionLocal
from core.models import Role
from repositories.user_repository import UserRepository
from services.auth_service import AuthService


def migrate_legacy_roles() -> None:
    """Роли `mentor`/`moderator` убраны из Role enum (см. историю продукта —
    остались 4 роли: пользователь/поисковик/краевед/админ). Alembic в проекте
    нет, поэтому переносим осевшие в БД старые значения сюда — идемпотентно,
    безопасно гонять на каждом старте (в т.ч. на проде после деплоя).

    Раньше `moderator` давал стафф-права наравне с `is_root` — намеренно НЕ
    повышаем таких пользователей до `is_root` автоматически (это была бы
    молчаливая эскалация прав); если нужно — администратор выставит `is_root`
    вручную через `PATCH /admin/users/{id}/root`.
    """
    with SessionLocal() as db:
        db.execute(
            text("UPDATE users SET role = 'local_historian' WHERE role IN ('mentor', 'moderator')")
        )
        db.commit()


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
            email=email, password=settings.bootstrap_root_password, role=Role.family
        )
        user.is_root = True
        db.commit()
