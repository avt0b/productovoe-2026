from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from api.deps import AuthServiceDep, CurrentUser
from api.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from api.schemas.user import PasswordChange, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_pair(tokens) -> TokenPair:
    return TokenPair(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, service: AuthServiceDep) -> UserOut:
    user = service.register(email=payload.email, password=payload.password, role=payload.role)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, service: AuthServiceDep) -> TokenPair:
    return _to_pair(service.login(email=payload.email, password=payload.password))


@router.post("/login/form", response_model=TokenPair, include_in_schema=False)
def login_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], service: AuthServiceDep
) -> TokenPair:
    """Форма для кнопки Authorize в Swagger (username = email)."""
    return _to_pair(service.login(email=form.username, password=form.password))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, service: AuthServiceDep) -> TokenPair:
    return _to_pair(service.refresh(payload.refresh_token))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, service: AuthServiceDep) -> None:
    service.logout(payload.refresh_token)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChange, user: CurrentUser, service: AuthServiceDep
) -> None:
    service.change_password(
        user, current_password=payload.current_password, new_password=payload.new_password
    )
