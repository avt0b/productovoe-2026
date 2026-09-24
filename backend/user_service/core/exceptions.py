from fastapi import status


class AppError(Exception):
    """Базовая доменная ошибка. API-слой превращает её в HTTP-ответ."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "Ошибка приложения"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class ProfileNotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Профиль не найден"


class NotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Объект не найден"


class PermissionDenied(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Недостаточно прав"


class Conflict(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Конфликт состояния"


class ServiceUnavailable(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Хранилище файлов недоступно"
