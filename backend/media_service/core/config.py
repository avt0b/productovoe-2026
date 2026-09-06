from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://marshruty:marshruty@127.0.0.1:5432/media"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth_service"

    # Токен воркера рендера; пусто -> дёргать может moderator/root.
    render_worker_token: str = ""


settings = Settings()
