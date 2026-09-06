"""Управление учётными записями администраторов (доступно superadmin)."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from core import security
from core.exceptions import AdminNotFound, EmailAlreadyExists, LastSuperadmin, PermissionDenied
from core.models import AdminRole, AdminUser
from repositories.admin_repository import AdminRepository
from repositories.session_repository import SessionRepository


class AccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.admins = AdminRepository(db)
        self.sessions = SessionRepository(db)

    def search(self, **filters) -> tuple[Sequence[AdminUser], int]:
        return self.admins.search(**filters)

    def get(self, admin_id: str) -> AdminUser:
        admin = self.admins.get(admin_id)
        if admin is None:
            raise AdminNotFound
        return admin

    def create(
        self, *, email: str, password: str, full_name: str, role: AdminRole
    ) -> AdminUser:
        email = email.strip().lower()
        if self.admins.exists_by_email(email):
            raise EmailAlreadyExists
        admin = self.admins.add(
            AdminUser(
                email=email,
                password_hash=security.hash_password(password),
                full_name=full_name,
                role=role,
            )
        )
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def update(self, admin_id: str, data: dict) -> AdminUser:
        admin = self.get(admin_id)
        if "role" in data and data["role"] != admin.role:
            self._ensure_not_last_superadmin(admin)
        for field, value in data.items():
            setattr(admin, field, value)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def set_active(self, actor: AdminUser, admin_id: str, is_active: bool) -> AdminUser:
        admin = self.get(admin_id)
        if admin.id == actor.id and not is_active:
            raise PermissionDenied("Нельзя отключить самого себя")
        if not is_active:
            self._ensure_not_last_superadmin(admin)
            self.sessions.revoke_all_for(admin.id)
        admin.is_active = is_active
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def reset_password(self, admin_id: str, new_password: str) -> AdminUser:
        """Сброс пароля суперадмином: все сессии администратора гасятся."""
        admin = self.get(admin_id)
        admin.password_hash = security.hash_password(new_password)
        self.sessions.revoke_all_for(admin.id)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def reset_totp(self, admin_id: str) -> AdminUser:
        """Снять 2FA — когда администратор потерял телефон и коды восстановления.

        Сессии гасятся: при следующем входе он настроит TOTP заново.
        """
        admin = self.get(admin_id)
        admin.totp_enabled = False
        admin.totp_secret = None
        admin.totp_confirmed_at = None
        self.admins.replace_recovery_codes(admin.id, [])
        self.sessions.revoke_all_for(admin.id)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def delete(self, actor: AdminUser, admin_id: str) -> None:
        admin = self.get(admin_id)
        if admin.id == actor.id:
            raise PermissionDenied("Нельзя удалить самого себя")
        self._ensure_not_last_superadmin(admin)
        self.admins.delete(admin)
        self.db.commit()

    # --- helpers ---

    def _ensure_not_last_superadmin(self, admin: AdminUser) -> None:
        if admin.role is not AdminRole.superadmin or not admin.is_active:
            return
        if self.admins.count_active_superadmins(exclude_id=admin.id) == 0:
            raise LastSuperadmin
