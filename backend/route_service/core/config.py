from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://marshruty:marshruty@127.0.0.1:5432/routes"

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

    # --- подсказка «рядом есть неподтверждённая заметка» (архив ↔ маршруты) ---
    archive_service_url: str = "http://127.0.0.1:8005"
    # Как далеко от точки маршрута заметка ещё считается «рядом».
    archive_nearby_radius_km: float = 2.0
    upstream_timeout_seconds: float = 3.0

    # --- автогенерация маршрута из слоя «ВОВ» map_service (модуль 2 ТЗ) ---
    map_service_url: str = "http://127.0.0.1:8003"

    # --- подсказка «оживить фото» у точки маршрута (маршруты ↔ «Живое фото») ---
    media_service_url: str = "http://127.0.0.1:8007"

    # --- достижение за первый пройденный маршрут (геймификация) ---
    user_service_url: str = "http://127.0.0.1:8002"

    # --- файлы (обложки маршрутов, аудио точек) в MinIO ---
    minio_endpoint: str = "http://127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "routes"
    minio_public_base_url: str | None = None


settings = Settings()
