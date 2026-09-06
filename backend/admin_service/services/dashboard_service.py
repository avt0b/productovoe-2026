"""Сборка дашборда: веерный опрос сервисов и сведение в плитки KPI.

Правило: недоступный сервис не роняет дашборд. Его плитки приходят с
`null`, а имя сервиса попадает в `degraded` — фронт рисует прочерк.
"""

import asyncio
from datetime import UTC, datetime

import httpx

from core.exceptions import UpstreamUnavailable
from services.upstream import SERVICES, Upstream


def _stats(block: dict | None) -> dict | None:
    if not block or not block.get("available"):
        return None
    return block.get("stats") or {}


class DashboardService:
    def __init__(self, upstream: Upstream) -> None:
        self.upstream = upstream

    async def overview(self) -> dict:
        services = await self.upstream.all_stats()

        auth = _stats(services.get("auth_service"))
        user = _stats(services.get("user_service"))
        map_ = _stats(services.get("map_service"))
        route = _stats(services.get("route_service"))
        hq = _stats(services.get("search_hq_service"))
        archive = _stats(services.get("archive_service"))
        media = _stats(services.get("media_service"))

        last_stand_by_status = (map_ or {}).get("last_stand_by_status", {})
        confirmed = last_stand_by_status.get("archive_confirmed", 0) + last_stand_by_status.get(
            "remains_raised", 0
        )

        # Плитки в том же порядке, что и в макете админки.
        tiles = [
            {
                "key": "users_total",
                "label": "Пользователи всего",
                "value": (auth or {}).get("users_total") if auth else None,
                "hint": f"+{(auth or {}).get('registered_7d', 0)} за 7 дней" if auth else None,
                "tone": "neutral",
            },
            {
                "key": "role_verification_queue",
                "label": "На верификации ролей",
                "value": (user or {}).get("pending_verification") if user else None,
                "hint": self._role_hint(user),
                "tone": "attention",
            },
            {
                "key": "moderation_queue",
                "label": "Очередь модерации",
                "value": (archive or {}).get("moderation_queue") if archive else None,
                "hint": f"подтверждено за неделю: {(archive or {}).get('verified_7d', 0)}"
                if archive
                else None,
                "tone": "attention",
            },
            {
                "key": "last_stand_points",
                "label": "Точки «Последнего боя»",
                "value": (map_ or {}).get("last_stand_total") if map_ else None,
                "hint": f"{confirmed} подтверждено архивом" if map_ else None,
                "tone": "neutral",
            },
            {
                "key": "active_expeditions",
                "label": "Активные экспедиции",
                "value": (hq or {}).get("trips_upcoming") if hq else None,
                "hint": f"{(hq or {}).get('registrations_active', 0)} участников записано"
                if hq
                else None,
                "tone": "neutral",
            },
            {
                "key": "media_queue",
                "label": "Очередь «Живого фото»",
                "value": (media or {}).get("queue_depth") if media else None,
                "hint": f"ошибок генерации: {(media or {}).get('failed', 0)}" if media else None,
                "tone": "error" if (media or {}).get("failed") else "neutral",
            },
        ]

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "tiles": tiles,
            "summary": {
                "users_total": (auth or {}).get("users_total"),
                "users_active": (auth or {}).get("users_active"),
                "users_by_role": (auth or {}).get("by_role"),
                "profiles_verified": (user or {}).get("verified"),
                "subscribed_to_search": (user or {}).get("subscribed_to_search"),
                "poi_total": (map_ or {}).get("poi_total"),
                "last_stand_total": (map_ or {}).get("last_stand_total"),
                "last_stand_by_status": last_stand_by_status or None,
                "moderation_queue": (archive or {}).get("moderation_queue"),
                "routes_published": (route or {}).get("published"),
                "squads_total": (hq or {}).get("squads_total"),
                "funds_collected": (hq or {}).get("funds_collected"),
                "funds_target": (hq or {}).get("funds_target"),
                "media_queue_depth": (media or {}).get("queue_depth"),
            },
            "services": services,
            "degraded": [name for name, block in services.items() if not block.get("available")],
            # Экран «Источники и импорт» из макета требует отдельного сервиса
            # импорта Книг Памяти — его в бэкенде ещё нет.
            "not_implemented": ["ingest_service"],
        }

    async def timeseries(self, days: int = 30) -> dict:
        """Ряды для графика «Динамика верификации и внесения персоналий»."""

        async def series(service: str) -> list[dict]:
            # Недоступный сервис отдаёт пустой ряд, а не роняет весь график.
            try:
                data = await self.upstream.call(
                    service, "GET", "/internal/stats/timeseries", params={"days": days}
                )
            except (UpstreamUnavailable, httpx.HTTPError):
                return []
            return (data or {}).get("points", []) if isinstance(data, dict) else []

        last_stand, archive_entries, registrations = await asyncio.gather(
            series("map"), series("archive"), series("auth")
        )
        return {
            "days": days,
            "series": [
                {"key": "last_stand_added", "label": "Точки «Последнего боя»", "points": last_stand},
                {"key": "entries_verified", "label": "Проверено записей", "points": archive_entries},
                {"key": "registrations", "label": "Регистрации", "points": registrations},
            ],
        }

    async def health(self) -> dict:
        rows = await self.upstream.all_health()
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "services": rows,
            "healthy": sum(1 for r in rows if r["ok"]),
            "total": len(SERVICES),
        }

    @staticmethod
    def _role_hint(user: dict | None) -> str | None:
        if not user:
            return None
        by_role = user.get("pending_verification_by_role") or {}
        if not by_role:
            return None
        names = {
            "local_historian": "краеведов",
            "searcher": "поисковиков",
            "mentor": "наставников",
        }
        parts = [f"{count} {names.get(role, role)}" for role, count in by_role.items() if count]
        return ", ".join(parts) or None
