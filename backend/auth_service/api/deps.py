from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.db import get_db
from core.models import Role, User
from core.security import decode_access_token
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.user_service import UserAdminService

DbSession = Annotated[Session, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/form", auto_error=True)


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


def get_user_admin_service(db: DbSession) -> UserAdminService:
    return UserAdminService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserAdminServiceDep = Annotated[UserAdminService, Depends(get_user_admin_service)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise creds_exc

    user = UserRepository(db).get(payload.get("sub"))
    if user is None or not user.is_active:
        raise creds_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_root(user: CurrentUser) -> User:
    if not user.is_root:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора"
        )
    return user


def require_roles(*roles: Role):
    allowed = set(roles)

    def _dep(user: CurrentUser) -> User:
        if user.is_root or user.role in allowed:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Требуется одна из ролей: {', '.join(r.value for r in allowed)}",
        )

    return _dep
