from collections.abc import Sequence

from sqlalchemy.orm import Session

from core.exceptions import Conflict, NotFound, PermissionDenied
from core.models import ApplicationStatus, Profile, RoleApplication
from core.security import Principal
from repositories.profile_repository import ProfileRepository
from repositories.role_application_repository import RoleApplicationRepository
from services import auth_client

# Названия ролей для сообщений человеку: «дождитесь решения по заявке на роль
# «краевед»» понятнее, чем local_historian.
ROLE_TITLES = {"searcher": "поисковик", "local_historian": "краевед", "family": "семья"}


class RoleApplicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RoleApplicationRepository(db)
        self.profiles = ProfileRepository(db)

    def submit(self, principal: Principal, data: dict) -> RoleApplication:
        requested_role = data["requested_role"]
        if principal.role == requested_role or principal.is_root:
            raise Conflict("У вас уже есть эта роль")
        # Роль у человека одна, и одобрение её заменяет. Две заявки в очереди
        # разом — это два одобрения подряд, из которых второе молча стирает
        # первое: человек просил и то и другое, а получил только последнее.
        # Поэтому в работе всегда не больше одной заявки.
        pending = self.repo.pending(principal.user_id)
        if pending is not None:
            if pending.requested_role == requested_role:
                raise Conflict("Заявка на эту роль уже на рассмотрении")
            raise Conflict(
                f"Сначала дождитесь решения по заявке на роль «{ROLE_TITLES.get(pending.requested_role, pending.requested_role)}»"
            )
        application = self.repo.add(RoleApplication(user_id=principal.user_id, **data))
        self.db.commit()
        self.db.refresh(application)
        return application

    def list_mine(self, principal: Principal) -> Sequence[RoleApplication]:
        return self.repo.for_user(principal.user_id)

    def search(
        self, *, status: ApplicationStatus | None = None, limit: int = 50, offset: int = 0
    ) -> Sequence[RoleApplication]:
        return self.repo.search(status=status, limit=limit, offset=offset)

    def decide(
        self, actor: Principal, application_id: str, *, approve: bool, note: str = ""
    ) -> RoleApplication:
        if not actor.is_root:
            raise PermissionDenied("Решение по заявке принимает только администратор")
        application = self.repo.get(application_id)
        if application is None:
            raise NotFound("Заявка не найдена")
        if application.status is not ApplicationStatus.pending:
            raise Conflict("Заявка уже рассмотрена")

        application.status = ApplicationStatus.approved if approve else ApplicationStatus.rejected
        application.review_note = note
        application.reviewed_by = actor.user_id

        if approve:
            # Синхронно и с пробросом ошибки — если auth_service недоступен,
            # решение админа не должно тихо потеряться на середине пути.
            auth_client.set_role(user_id=application.user_id, role=application.requested_role)
            profile = self.profiles.get(application.user_id)
            if profile is None:
                profile = self.profiles.add(
                    Profile(id=application.user_id, role=application.requested_role)
                )
            else:
                # Что роль заменила — видно и админу, и человеку в своей заявке.
                application.previous_role = profile.role
                profile.role = application.requested_role
            profile.is_verified = True

        self.db.commit()
        self.db.refresh(application)
        return application
