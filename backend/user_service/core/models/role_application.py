import enum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base, TimestampMixin, new_uuid


class ApplicationStatus(str, enum.Enum):
    """Решение по заявке — закрытый набор, в отличие от свободных строк
    вроде Notification.kind."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# Роли, которые можно попросить — обе не самоназначаемые при регистрации
# (см. auth_service/api/schemas/user.py: SELF_ASSIGNABLE_ROLES = {family}).
REQUESTABLE_ROLES = {"searcher", "local_historian"}


class RoleApplication(TimestampMixin, Base):
    """Заявка на роль поисковика или краеведа — пользователь прикладывает
    контакты и доказательства, администратор одобряет или отклоняет.

    requested_role — свободная строка, а не FK на auth_service.Role (тот же
    принцип, что у Profile.role): источник истины по ролям — auth_service,
    здесь только сама заявка и её статус."""

    __tablename__ = "role_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    requested_role: Mapped[str] = mapped_column(String(32), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    # Телефон/telegram/иной способ связи — свободный текст, не структурируем.
    contact: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    # Описание опыта/доказательств ("состою в отряде «Высота» с 2019...").
    evidence: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Ссылка на фото/документ через уже существующий POST /uploads.
    evidence_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", native_enum=False, length=16),
        default=ApplicationStatus.pending,
        nullable=False,
    )
    review_note: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    # Роль, которая была у человека в момент одобрения. Роль одна, и одобрение
    # её заменяет — без этой записи подмена происходила бы бесследно: и админ,
    # и человек видели бы только новую.
    previous_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
