from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import decode_access_token

_bearer = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    is_root: bool


def get_principal(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> Principal:
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Principal(
        user_id=payload["sub"],
        role=payload.get("role", "family"),
        is_root=bool(payload.get("is_root", False)),
    )


CurrentPrincipal = Annotated[Principal, Depends(get_principal)]


def require_root(principal: CurrentPrincipal) -> Principal:
    if not principal.is_root:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора"
        )
    return principal
