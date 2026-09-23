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

    # --- MinIO: куда кладём готовый ролик ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "media"
    minio_public_base_url: str | None = None

    poll_interval_seconds: float = 5.0
    upstream_timeout_seconds: float = 60.0
    # Сколько ждать рендера на Replicate, прежде чем считать заявку неудавшейся.
    render_timeout_seconds: float = 300.0


settings = Settings()
