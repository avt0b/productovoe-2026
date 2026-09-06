"""Клиент служебной плоскости `/internal/*` остальных сервисов.

Админка сама не лезет в чужие базы: она ходит по HTTP с внутренним ключом
и заголовком `X-Actor-Id`, чтобы в `created_by` / `verified_by` осел настоящий
администратор, а бизнес-правила сервисов сработали как обычно.
"""

import asyncio
from dataclasses import dataclass

import httpx

from core.config import settings
from core.exceptions import UpstreamUnavailable


@dataclass(frozen=True)
class ServiceRef:
    key: str  # короткий ключ для маршрутизации
    name: str  # имя сервиса, как он сам себя называет в /health
    base_url: str
    title: str  # для UI


def _registry() -> dict[str, ServiceRef]:
    return {
        s.key: s
        for s in (
            ServiceRef("auth", "auth_service", settings.auth_service_url, "Аутентификация"),
            ServiceRef("user", "user_service", settings.user_service_url, "Профили"),
            ServiceRef("map", "map_service", settings.map_service_url, "Карта и «Последний бой»"),
            ServiceRef("route", "route_service", settings.route_service_url, "Маршруты"),
            ServiceRef(
                "search_hq",
                "search_hq_service",
                settings.search_hq_service_url,
                "Поисковый штаб",
            ),
            ServiceRef(
                "archive", "archive_service", settings.archive_service_url, "Народный архив"
            ),
            ServiceRef("media", "media_service", settings.media_service_url, "«Живое фото»"),
        )
    }


SERVICES = _registry()


class Upstream:
    """Обёртка над одним общим AsyncClient (живёт столько же, сколько приложение)."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.upstream_timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- низкий уровень ---

    def _resolve(self, service: str) -> ServiceRef:
        ref = SERVICES.get(service)
        if ref is None:
            raise UpstreamUnavailable(f"Неизвестный сервис: {service}")
        return ref

    def _headers(self, actor_id: str | None) -> dict[str, str]:
        headers = {"X-Internal-Key": settings.internal_api_key}
        if actor_id:
            headers["X-Actor-Id"] = actor_id
        return headers

    async def request(
        self,
        service: str,
        method: str,
        path: str,
        *,
        actor_id: str | None = None,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        ref = self._resolve(service)
        try:
            response = await self._client.request(
                method,
                f"{ref.base_url}{path}",
                headers=self._headers(actor_id),
                params=params,
                json=json,
            )
        except httpx.HTTPError as exc:
            raise UpstreamUnavailable(f"{ref.name} недоступен: {exc.__class__.__name__}")
        return response

    async def call(
        self,
        service: str,
        method: str,
        path: str,
        *,
        actor_id: str | None = None,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list | None:
        """Как `request`, но разворачивает ошибку сервиса в доменную."""
        response = await self.request(
            service, method, path, actor_id=actor_id, params=params, json=json
        )
        if response.status_code >= 400:
            detail = self._detail_of(response)
            raise UpstreamUnavailable(detail)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    @staticmethod
    def _detail_of(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return f"Сервис ответил {response.status_code}"
        if isinstance(body, dict) and "detail" in body:
            return str(body["detail"])
        return f"Сервис ответил {response.status_code}"

    # --- сбор статистики ---

    async def _safe_stats(self, ref: ServiceRef) -> dict:
        """Один сервис не должен ронять весь дашборд."""
        try:
            response = await self._client.get(
                f"{ref.base_url}/internal/stats", headers=self._headers(None)
            )
            if response.status_code >= 400:
                return {
                    "available": False,
                    "title": ref.title,
                    "error": self._detail_of(response),
                }
            return {"available": True, "title": ref.title, "stats": response.json()}
        except httpx.HTTPError as exc:
            return {
                "available": False,
                "title": ref.title,
                "error": f"недоступен ({exc.__class__.__name__})",
            }

    async def all_stats(self) -> dict[str, dict]:
        refs = list(SERVICES.values())
        results = await asyncio.gather(*(self._safe_stats(ref) for ref in refs))
        return {ref.name: result for ref, result in zip(refs, results, strict=True)}

    async def _safe_health(self, ref: ServiceRef) -> dict:
        try:
            response = await self._client.get(f"{ref.base_url}/health")
            payload = response.json() if response.content else {}
            return {
                "service": ref.name,
                "title": ref.title,
                "url": ref.base_url,
                "ok": response.status_code == 200,
                "status": payload.get("status", str(response.status_code)),
                "env": payload.get("env", ""),
            }
        except httpx.HTTPError as exc:
            return {
                "service": ref.name,
                "title": ref.title,
                "url": ref.base_url,
                "ok": False,
                "status": f"недоступен ({exc.__class__.__name__})",
                "env": "",
            }

    async def all_health(self) -> list[dict]:
        return list(await asyncio.gather(*(self._safe_health(r) for r in SERVICES.values())))
