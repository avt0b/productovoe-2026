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

    # auth_client.set_role — применяет решение по RoleApplication.
    auth_service_url: str = "http://127.0.0.1:8001"

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

    # --- файлы (аватары) в MinIO, S3-совместимое хранилище ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "users"
    minio_public_base_url: str | None = None

    # --- push-доставка (FCM HTTP v1) ---
    # Без project_id и ключа push просто не уходит — лента уведомлений и
    # ачивки работают как раньше, это не блокирующая зависимость.
    fcm_project_id: str | None = None
    # Ключ сервисного аккаунта (Firebase Console → Project settings → Service
    # accounts → Generate new private key). Либо путь к файлу на диске
    # (удобно локально), либо всё содержимое JSON одной строкой (удобно как
    # секрет в докере/CI, без монтирования файла) — заполнено то, что есть.
    fcm_credentials_path: str | None = None
    fcm_credentials_json: str | None = None
    upstream_timeout_seconds: float = 5.0


settings = Settings()
