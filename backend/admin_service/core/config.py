from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://marshruty:marshruty@127.0.0.1:5432/admin"

    # --- JWT админки -------------------------------------------------------
    # Секрет и issuer СВОИ, не общие с auth_service: токен админки не должен
    # приниматься публичными сервисами, и наоборот.
    admin_jwt_secret: str = "dev-admin-secret-change-me"
    admin_jwt_algorithm: str = "HS256"
    admin_jwt_issuer: str = "admin_service"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 7
    # Промежуточный токен между вводом пароля и вводом кода из приложения.
    mfa_token_ttl_minutes: int = 5

    # --- TOTP (двухфакторная аутентификация) -------------------------------
    totp_issuer_name: str = "Маршруты победы"
    totp_valid_window: int = 1  # ±30 секунд к текущему окну
    # При True админ без настроенного TOTP не может ничего, кроме его настройки.
    require_totp: bool = True
    recovery_codes_count: int = 10

    # --- Защита от перебора пароля ----------------------------------------
    max_failed_attempts: int = 5
    lockout_minutes: int = 15

    # --- Служебная плоскость сервисов -------------------------------------
    internal_api_key: str = "dev-internal-key-change-me"
    upstream_timeout_seconds: float = 5.0

    auth_service_url: str = "http://127.0.0.1:8001"
    user_service_url: str = "http://127.0.0.1:8002"
    map_service_url: str = "http://127.0.0.1:8003"
    route_service_url: str = "http://127.0.0.1:8006"
    search_hq_service_url: str = "http://127.0.0.1:8004"
    archive_service_url: str = "http://127.0.0.1:8005"
    media_service_url: str = "http://127.0.0.1:8007"

    # Веб-админка (Vue). В .env — JSON-массив: ["http://localhost:5173"]
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Первый superadmin создаётся на старте, если оба поля заданы.
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None


settings = Settings()
