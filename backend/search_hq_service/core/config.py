from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+psycopg://marshruty:marshruty@127.0.0.1:5432/search_hq"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth_service"

    # Внутренний служебный ключ: по нему admin_service ходит в /internal/*.
    internal_api_key: str = "dev-internal-key-change-me"

    # --- достижения за выезд и донат (геймификация) ---
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

    # --- экскурсии и бамп ---
    # Как далеко от точки экскурсии можно открыть сбор и трясти телефон, в метрах.
    excursion_site_radius_m: float = 150.0
    # Сколько погрешности GPS засчитывать человеку сверх радиуса, не больше, в метрах.
    bump_accuracy_slack_m: float = 50.0
    # Сколько идёт сбор группы после «Начать сбор», в минутах.
    gathering_duration_minutes: int = 30
    # Через сколько часов после выхода группы экскурсия считается законченной,
    # даже если краевед забыл нажать «Завершить»: иначе телефоны группы так и
    # слали бы свои координаты до вечера.
    walk_duration_hours: int = 4
    # Точка человека старше этого на карте группы не показывается: он отстал,
    # закрыл приложение или потерял сеть — метка «вот он» врала бы.
    walk_position_ttl_seconds: int = 120
    # На сколько секунд могут разойтись встряски краеведа и участника.
    # Три секунды, а не полторы: на живом сборе краевед обходит группу и
    # трясёт телефон не по секундомеру, а когда человек догадался достать свой.
    bump_window_seconds: float = 3.0
    # Сколько секунд запрос встряски ждёт встряску другой стороны.
    # Заведомо дольше окна: иначе первый успеет получить «пары нет» раньше,
    # чем окно закроется, и совпадение пропадёт на ровном месте.
    bump_wait_seconds: float = 3.5

    # --- «Я потерялся» ---
    # Сколько живёт тревога, если её никто не закрыл: прогулка столько не длится,
    # а висящий «поиск» через полдня только пугает.
    lost_alert_ttl_minutes: int = 120

    # --- модерация чата ---
    # Доп. запрещённые слова/фразы сверх встроенного мат-фильтра, через запятую.
    # Пусто по умолчанию — что банить сверх мата, решает оператор площадки, не код.
    chat_banned_words: str = ""

    # --- платежи (ЮKassa) ---
    # Без shop_id/secret_key донат учитывается сразу в БД — как раньше, без шлюза.
    # Задав оба (в проде — боевые ключи, в тесте — ключи из личного кабинета в режиме
    # тестового магазина), донат уходит через ЮKassa: pending → вебхук/подтверждение → succeeded.
    yookassa_shop_id: str | None = None
    yookassa_secret_key: str | None = None
    yookassa_api_base: str = "https://api.yookassa.ru/v3"
    yookassa_return_url: str = "https://marshruty.ru/payments/return"


settings = Settings()
