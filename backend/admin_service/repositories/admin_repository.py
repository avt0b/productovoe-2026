from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.models import AdminRole, AdminUser, RecoveryCode


class AdminRepository:
    """Доступ к таблицам администраторов и кодов восстановления. Только SQL."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- учётки ---

    def get(self, admin_id: str) -> AdminUser | None:
        return self.db.get(AdminUser, admin_id)

    def get_by_email(self, email: str) -> AdminUser | None:
        return self.db.scalar(select(AdminUser).where(AdminUser.email == email))

    def exists_by_email(self, email: str) -> bool:
        return self.db.scalar(select(AdminUser.id).where(AdminUser.email == email)) is not None

    def search(
        self,
        *,
        query: str | None = None,
        role: AdminRole | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[AdminUser], int]:
        conditions = []
        if query:
            pattern = f"%{query.strip()}%"
            conditions.append(AdminUser.email.ilike(pattern) | AdminUser.full_name.ilike(pattern))
        if role is not None:
            conditions.append(AdminUser.role == role)
        if is_active is not None:
            conditions.append(AdminUser.is_active.is_(is_active))

        total = self.db.scalar(select(func.count(AdminUser.id)).where(*conditions)) or 0
        rows = self.db.scalars(
            select(AdminUser)
            .where(*conditions)
            .order_by(AdminUser.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return rows, total

    def add(self, admin: AdminUser) -> AdminUser:
        self.db.add(admin)
        self.db.flush()
        return admin

    def delete(self, admin: AdminUser) -> None:
        self.db.delete(admin)

    def count_active_superadmins(self, *, exclude_id: str | None = None) -> int:
        conditions = [
            AdminUser.role == AdminRole.superadmin,
            AdminUser.is_active.is_(True),
        ]
        if exclude_id:
            conditions.append(AdminUser.id != exclude_id)
        return self.db.scalar(select(func.count(AdminUser.id)).where(*conditions)) or 0

    # --- коды восстановления ---

    def replace_recovery_codes(self, admin_id: str, code_hashes: list[str]) -> None:
        for row in self.db.scalars(
            select(RecoveryCode).where(RecoveryCode.admin_id == admin_id)
        ).all():
            self.db.delete(row)
        self.db.flush()
        for code_hash in code_hashes:
            self.db.add(RecoveryCode(admin_id=admin_id, code_hash=code_hash))
        self.db.flush()

    def get_unused_recovery_code(self, admin_id: str, code_hash: str) -> RecoveryCode | None:
        return self.db.scalar(
            select(RecoveryCode).where(
                RecoveryCode.admin_id == admin_id,
                RecoveryCode.code_hash == code_hash,
                RecoveryCode.used_at.is_(None),
            )
        )

    def count_unused_recovery_codes(self, admin_id: str) -> int:
        return (
            self.db.scalar(
                select(func.count(RecoveryCode.id)).where(
                    RecoveryCode.admin_id == admin_id, RecoveryCode.used_at.is_(None)
                )
            )
            or 0
        )
