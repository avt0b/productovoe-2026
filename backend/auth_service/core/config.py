from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/auth"

    # JWT. На хакатоне — HS256 с общим секретом (проще раздать сервисам).
    # Прод-апгрейд: RS256, приватный ключ только здесь.
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth_service"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # Bootstrap первого администратора (is_root=true) при старте.
    bootstrap_root_email: str | None = None
    bootstrap_root_password: str | None = None

    # Внутренний служебный ключ: по нему admin_service ходит в /internal/*.
    internal_api_key: str = "dev-internal-key-change-me"


settings = Settings()
