from fastapi import APIRouter, status

from api.deps import CurrentPrincipal, RoleApplicationServiceDep
from api.schemas.role_application import RoleApplicationCreate, RoleApplicationOut

router = APIRouter(prefix="/role-applications", tags=["role-applications (заявки на роль)"])


@router.get("/mine", response_model=list[RoleApplicationOut])
def my_applications(
    principal: CurrentPrincipal, service: RoleApplicationServiceDep
) -> list[RoleApplicationOut]:
    return [RoleApplicationOut.model_validate(a) for a in service.list_mine(principal)]


@router.post("", response_model=RoleApplicationOut, status_code=status.HTTP_201_CREATED)
def submit_application(
    payload: RoleApplicationCreate,
    principal: CurrentPrincipal,
    service: RoleApplicationServiceDep,
) -> RoleApplicationOut:
    return RoleApplicationOut.model_validate(service.submit(principal, payload.model_dump()))
