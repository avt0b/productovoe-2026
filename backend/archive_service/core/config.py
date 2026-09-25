from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://marshruty:marshruty@127.0.0.1:5432/archive"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth_service"

    # Внутренний служебный ключ: по нему admin_service ходит в /internal/*.
    internal_api_key: str = "dev-internal-key-change-me"

    # --- достижение за помощь в верификации записи (геймификация) ---
    user_service_url: str = "http://127.0.0.1:8002"
    upstream_timeout_seconds: float = 3.0

    # Клиентское приложение ходит в сервис напрямую: dev-сервер Vite и APK
    # (Capacitor на Android отдаёт приложение с https://localhost, а на стенде
    # с сервисами по http — с http://localhost).
    cors_origins: list[str] = [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost",
        "https://localhost",
        "capacitor://localhost",
    ]

    # --- файлы (фото к записям архива) в MinIO, S3-совместимое хранилище ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "archive"
    # Публично доступный извне адрес того же MinIO (браузер должен уметь его открыть).
    # Локально порт MinIO проброшен на хост — endpoint и так подходит.
    minio_public_base_url: str | None = None


settings = Settings()
