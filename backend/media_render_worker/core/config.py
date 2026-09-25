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

    # --- Оживление фото: Kling AI Avatar 2.0 через шлюз Ranvik ---
    ranvik_api_key: str = ""
    ranvik_api_base: str = "https://api.ranvik.ru/v1"
    # Говорящий портрет: фото + голос -> боец произносит текст. Из опробованных
    # (P-Video, Seedance 1.5 Pro, LTX) только он моргал и не «наезжал» камерой.
    ranvik_model: str = "kling-avatar-20"
    # Необязательная подсказка модели про мимику — губы и так идут за голосом.
    # По-английски — так модели понимают лучше.
    avatar_prompt: str = (
        "The person speaks calmly and warmly, with natural blinking, subtle head movements "
        "and a gentle, kind expression. Static camera."
    )
    # Цена — за секунду голоса (5.81 ₽/сек на момент выбора), а текст с подвигом
    # из архива бывает до 2000 символов (~2.5 мин, ~850 ₽). Режем до ~30 сек
    # речи (~175 ₽ максимум) — по концу предложения, см. worker._limit_narration.
    max_narration_chars: int = 400
    # Пробный режим: в Ranvik не ходим, вместо ролика — заглушка «DRY RUN»
    # (assets/dry_run.mp4). Вся остальная цепочка — очередь, SpeechKit, MinIO,
    # ready/failed — настоящая. Чтобы проверить сервис целиком, не тратя денег.
    ranvik_dry_run: bool = False

    # --- MinIO: куда кладём готовый ролик ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "media"
    minio_public_base_url: str | None = None

    poll_interval_seconds: float = 5.0
    upstream_timeout_seconds: float = 60.0
    # Сколько ждать ролик (очередь у вендора + генерация), прежде чем считать
    # заявку неудавшейся.
    render_timeout_seconds: float = 900.0


settings = Settings()
