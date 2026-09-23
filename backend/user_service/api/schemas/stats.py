from pydantic import BaseModel, Field


class StatIncrementRequest(BaseModel):
    """Тело вызова из сервиса-источника события (route_service — маршрут
    завершён, search_hq_service — экскурсия завершилась, map_service/
    archive_service — новая находка). Не идемпотентно, в отличие от ачивок —
    каждый вызов реально прибавляет 1."""

    user_id: str = Field(min_length=1, max_length=36)
    metric: str = Field(min_length=1, max_length=64)


class StatIncrementOut(BaseModel):
    metric: str
    value: int
