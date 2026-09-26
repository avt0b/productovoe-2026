from sqlalchemy.orm import Session

from core.config import settings
from core.exceptions import Conflict, NotFound
from core.models import ApplicationStatus, Profile, RoleGrant
from core.role_keys import role_for_key
from repositories.profile_repository import ProfileRepository
from repositories.role_application_repository import RoleApplicationRepository
from services import auth_client


class RoleGrantService:
    """Роль по NFC-метке — для показа приложения: судье подносят метку, и он
    сразу поисковик или краевед, без заявки и администратора.

    Разрешение даёт сам ключ с метки, а не токен: кому выдать, приложение
    присылает uuid'ом. Последствия выдачи — те же, что у одобренной заявки
    (`RoleApplicationService.decide`): роль в auth_service, кэш роли и отметка
    «подтверждён» в профиле."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.profiles = ProfileRepository(db)
        self.applications = RoleApplicationRepository(db)

    def redeem(self, *, key: str, user_id: str, nickname: str) -> dict:
        found = role_for_key(key, settings.role_grant_keys)
        if found is None:
            raise NotFound("Метка не подходит")
        role, digest = found

        account = auth_client.get_user(user_id)
        if account is None:
            raise NotFound("Пользователь не найден")
        if account.get("is_root"):
            # Роль у человека одна: выдав админу «краеведа», метка молча
            # сняла бы с учётки всё остальное, что к роли привязано.
            raise Conflict("Администратору роль меткой не меняем")

        previous_role = account.get("role") or "family"
        already = previous_role == role
        if not already:
            auth_client.set_role(user_id=user_id, role=role)

        profile = self.profiles.get(user_id)
        if profile is None:
            profile = self.profiles.add(Profile(id=user_id, role=role))
        profile.role = role
        profile.is_verified = True

        # Заявка на эту же роль больше не ждёт решения — иначе в профиле
        # рядом с новой ролью висело бы «заявка на рассмотрении».
        pending = self.applications.pending(user_id, role)
        if pending is not None:
            pending.status = ApplicationStatus.approved
            pending.previous_role = previous_role
            pending.review_note = "Роль выдана NFC-меткой"

        self.db.add(
            RoleGrant(
                user_id=user_id,
                nickname=nickname,
                role=role,
                previous_role=previous_role,
                key_fingerprint=digest[:12],
            )
        )
        self.db.commit()
        return {
            "user_id": user_id,
            "role": role,
            "previous_role": previous_role,
            "already": already,
        }
