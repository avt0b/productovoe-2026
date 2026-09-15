from fastapi import status


class AppError(Exception):
    """Базовая доменная ошибка. API-слой превращает её в HTTP-ответ."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class EmailAlreadyExists(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Пользователь с таким email уже зарегистрирован"


class InvalidCredentials(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Неверный email или пароль"


class InactiveUser(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Учётная запись отключена"


class InvalidToken(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Недействительный токен"


class InvalidRefreshToken(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Недействительный refresh-токен"


class PermissionDenied(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Недостаточно прав"


class UserNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Пользователь не найден"


class WrongPassword(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Текущий пароль неверен"


# --- внешний вход: VK ID, MAX, Госуслуги ---


class ExternalProviderNotConfigured(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Этот способ входа не настроен"


class ExternalProviderError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "Провайдер входа ответил ошибкой"


class ExternalLoginNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Попытка входа не найдена — начните вход заново"


class ExternalLoginExpired(AppError):
    status_code = status.HTTP_410_GONE
    detail = "Время на вход вышло — начните заново"


class ExternalLoginFailed(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Вход не подтверждён"


class InvalidReturnUrl(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Вернуть после входа можно только в приложение"


class InvalidExternalResultCode(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Код подтверждения входа не подходит"
