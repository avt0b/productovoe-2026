from fastapi import status


class AppError(Exception):
    """Базовая доменная ошибка. API-слой превращает её в HTTP-ответ."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class InvalidCredentials(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Неверный email или пароль"


class AccountLocked(AppError):
    status_code = status.HTTP_423_LOCKED
    detail = "Учётная запись временно заблокирована после неудачных попыток входа"


class InactiveAdmin(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Учётная запись администратора отключена"


class InvalidToken(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Недействительный токен"


class InvalidRefreshToken(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Недействительный refresh-токен"


class InvalidTotpCode(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Неверный код подтверждения"


class TotpNotConfigured(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Двухфакторная аутентификация не настроена"


class TotpAlreadyEnabled(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Двухфакторная аутентификация уже включена"


class MfaRequired(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Требуется двухфакторная аутентификация"


class WrongPassword(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Текущий пароль неверен"


class EmailAlreadyExists(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Администратор с таким email уже существует"


class AdminNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Администратор не найден"


class PermissionDenied(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Недостаточно прав"


class LastSuperadmin(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Нельзя отключить или понизить последнего суперадминистратора"


class UpstreamUnavailable(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Сервис временно недоступен"
