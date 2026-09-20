from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/users"

    # Тот же секрет, что у auth_service (HS256) — для локальной проверки JWT.
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth_service"

    # Внутренний служебный ключ: по нему admin_service ходит в /internal/*.
    internal_api_key: str = "dev-internal-key-change-me"

    # Клиентское приложение ходит в сервис напрямую: dev-сервер Vite и APK
    # (Capacitor на Android отдаёт приложение с https://localhost).
    cors_origins: list[str] = [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://localhost",
        "capacitor://localhost",
    ]

    # --- файлы (аватары) в MinIO, S3-совместимое хранилище ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "users"
    minio_public_base_url: str | None = None


settings = Settings()
