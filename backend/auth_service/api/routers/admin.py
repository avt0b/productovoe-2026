from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.deps import UserAdminServiceDep, require_root
from api.schemas.user import RoleUpdate, UserOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_root)])


@router.get("/users", response_model=list[UserOut])
def list_users(
    service: UserAdminServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserOut]:
    return [UserOut.model_validate(u) for u in service.list_users(limit=limit, offset=offset)]


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, service: UserAdminServiceDep) -> UserOut:
    return UserOut.model_validate(service.get_user(user_id))


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_role(user_id: str, payload: RoleUpdate, service: UserAdminServiceDep) -> UserOut:
    return UserOut.model_validate(service.set_role(user_id, payload.role))


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_active(
    user_id: str,
    service: UserAdminServiceDep,
    is_active: Annotated[bool, Query()],
) -> UserOut:
    return UserOut.model_validate(service.set_active(user_id, is_active))


@router.patch("/users/{user_id}/root", response_model=UserOut)
def set_root(
    user_id: str,
    service: UserAdminServiceDep,
    is_root: Annotated[bool, Query()],
) -> UserOut:
    return UserOut.model_validate(service.set_root(user_id, is_root))
