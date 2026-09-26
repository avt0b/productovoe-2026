from fastapi import APIRouter

from api.deps import RoleGrantServiceDep
from api.schemas.role_grant import RoleGrantOut, RoleGrantRedeem

router = APIRouter(prefix="/role-grants", tags=["role-grants (роль NFC-меткой)"])


@router.post("/redeem", response_model=RoleGrantOut)
def redeem(payload: RoleGrantRedeem, service: RoleGrantServiceDep) -> RoleGrantOut:
    """Выдать роль по ключу с NFC-метки. Без токена: разрешение — сам ключ."""
    return RoleGrantOut(
        **service.redeem(
            key=payload.key,
            user_id=str(payload.user_id),
            nickname=payload.nickname.strip(),
        )
    )
