from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"

    # media_service: та же очередь, что и у /render/* в его собственном API.
    media_service_url: str = "http://127.0.0.1:8007"
    # Тот же токен, что RENDER_WORKER_TOKEN в media_service — иначе 403 на /render/*.
    render_worker_token: str = "dev-render-worker-token-change-me"

    # --- Yandex SpeechKit (синтез речи) ---
    yandex_api_key: str = ""
    yandex_folder_id: str = ""

    # --- Replicate (анимация фото + липсинк, модель SadTalker) ---
    replicate_api_token: str = ""
    # Версия модели на Replicate, например "cjwbw/sadtalker:<hash>" — берётся
    # со страницы модели (кнопка API), не меняется без явного решения.
    replicate_model_version: str = ""

    # --- Ranvik (агрегатор нейросетей с оплатой в рублях) ---
    # Беззвучное оживление фото на несколько секунд: моргнёт, вздохнёт,
    # повернёт голову. Дешевле и проще, чем голос + липсинк.
    ranvik_api_key: str = ""
    ranvik_api_base: str = "https://api.ranvik.ru/v1"
    ranvik_model: str = "seedance-15-pro"
    ranvik_duration_seconds: int = 5
    ranvik_resolution: str = "720p"

    # Кто оживляет фото: ranvik — беззвучно через Ranvik, replicate — голос
    # SpeechKit + липсинк SadTalker. auto — Ranvik, если задан его ключ.
    render_provider: Literal["auto", "ranvik", "replicate"] = "auto"

    # --- MinIO: куда кладём готовый ролик ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "media"
    minio_public_base_url: str | None = None

    poll_interval_seconds: float = 5.0
    upstream_timeout_seconds: float = 60.0
    # Сколько ждать рендера на Replicate, прежде чем считать заявку неудавшейся.
    # Холодный старт модели там — несколько минут; по истечении Replicate сам
    # отменяет прогон (заголовок Cancel-After), чтобы не платить за брошенный.
    render_timeout_seconds: float = 900.0

    @property
    def render_configured(self) -> bool:
        """Заданы ли все четыре ключа — без любого из них рендер не начинаем."""
        return all(
            value.strip()
            for value in (
                self.yandex_api_key,
                self.yandex_folder_id,
                self.replicate_api_token,
                self.replicate_model_version,
            )
        )

    @property
    def ranvik_configured(self) -> bool:
        return bool(self.ranvik_api_key.strip())

    @property
    def effective_render_provider(self) -> Literal["ranvik", "replicate"] | None:
        """Кем рендерить сейчас; `None` — ни у одного провайдера нет ключей."""
        if self.render_provider == "ranvik" or (
            self.render_provider == "auto" and self.ranvik_configured
        ):
            return "ranvik" if self.ranvik_configured else None
        return "replicate" if self.render_configured else None


settings = Settings()
