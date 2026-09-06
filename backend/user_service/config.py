from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/users"

    jwt_public_key_path: str = "./keys/jwt_public.pem"
    jwt_algorithm: str = "RS256"


settings = Settings()
