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

    # Клиентское приложение входит напрямую: dev-сервер Vite и APK
    # (Capacitor на Android отдаёт приложение с https://localhost, а на стенде
    # с сервисами по http — с http://localhost).
    cors_origins: list[str] = [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost",
        "https://localhost",
        "capacitor://localhost",
    ]

    # --- Внешний вход: VK ID, Яндекс ID, MAX, Госуслуги ---
    # Адрес этого сервиса, каким его видит браузер телефона: сюда провайдер вернёт человека.
    external_auth_public_url: str = "http://127.0.0.1:8001"
    # Сколько живёт попытка входа, секунд.
    external_auth_login_ttl_seconds: int = 600
    # Куда можно вернуть человека после входа — начало адреса. Всё остальное
    # отклоняется, иначе ручка стала бы открытым редиректом.
    external_auth_return_prefixes: list[str] = [
        "marshruty://",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://localhost",
    ]
    # Тестовые провайдеры для локальной разработки: страница «Войти как тестовый
    # пользователь» вместо настоящих VK ID, Яндекс ID, MAX и Госуслуг. В production не включаются.
    external_auth_mock: bool = False
    # Домен служебной почты у пользователей, пришедших через внешний вход.
    external_auth_email_domain: str = "external.marshruty.ru"

    # VK ID (id.vk.com): приложение регистрируется там же. Адреса ручек сверить с документацией.
    vk_id_client_id: str = ""
    vk_id_client_secret: str = ""
    vk_id_scope: str = "email"
    vk_id_authorize_url: str = "https://id.vk.com/authorize"
    vk_id_token_url: str = "https://id.vk.com/oauth2/auth"
    vk_id_user_info_url: str = "https://id.vk.com/oauth2/user_info"

    # Яндекс ID (oauth.yandex.ru): приложение регистрируется там же, доступы —
    # «Доступ к логину, имени и фамилии, полу», «к адресу почты», «к портрету».
    yandex_id_client_id: str = ""
    yandex_id_client_secret: str = ""
    # Пусто — берутся доступы, отмеченные в настройках приложения.
    yandex_id_scope: str = ""
    yandex_id_authorize_url: str = "https://oauth.yandex.ru/authorize"
    yandex_id_token_url: str = "https://oauth.yandex.ru/token"
    yandex_id_user_info_url: str = "https://login.yandex.ru/info"
    yandex_id_avatar_url_template: str = "https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200"

    # MAX: вход через бота. Бота публикует верифицированное юрлицо на платформе MAX.
    max_bot_name: str = ""
    max_webhook_secret: str = ""
    max_webhook_secret_header: str = "X-Max-Bot-Api-Secret"
    max_bot_link_template: str = "https://max.ru/{bot}?start={payload}"


settings = Settings()
