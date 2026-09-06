from core import security
from core.config import settings
from core.db import SessionLocal
from core.models import AdminRole, AdminUser
from repositories.admin_repository import AdminRepository


def ensure_bootstrap_admin() -> None:
    """Создаёт первого superadmin из настроек, если его ещё нет.

    TOTP при этом НЕ включён: администратор настраивает его сам при первом
    входе (при `REQUIRE_TOTP=true` без этого он никуда дальше не пройдёт).
    """
    if not (settings.bootstrap_admin_email and settings.bootstrap_admin_password):
        return

    email = settings.bootstrap_admin_email.strip().lower()
    with SessionLocal() as db:
        repo = AdminRepository(db)
        existing = repo.get_by_email(email)
        if existing is not None:
            if existing.role is not AdminRole.superadmin or not existing.is_active:
                existing.role = AdminRole.superadmin
                existing.is_active = True
                db.commit()
            return

        repo.add(
            AdminUser(
                email=email,
                password_hash=security.hash_password(settings.bootstrap_admin_password),
                full_name="Первый администратор",
                role=AdminRole.superadmin,
            )
        )
        db.commit()
