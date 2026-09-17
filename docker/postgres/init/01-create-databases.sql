-- Базы сервисов «Маршрутов победы» — по одной на сервис, имена как в DATABASE_URL
-- в docker-compose.yml.
--
-- Postgres выполняет файлы из этой папки один раз: при первом запуске с пустым
-- томом pg_data. Скрипт идёт от имени пользователя DB_USER, он и владелец баз.
-- Без него Postgres создаёт одну базу по имени DB_USER, и сервисы падают на старте:
-- `init_db` создаёт таблицы, но не саму базу.
--
-- Добавили сервис со своей базой — допишите её сюда и пересоздайте том
-- (`docker compose down -v`) или создайте базу руками на живом Postgres.

CREATE DATABASE auth;
CREATE DATABASE users;
CREATE DATABASE map;
CREATE DATABASE search_hq;
CREATE DATABASE archive;
CREATE DATABASE routes;
CREATE DATABASE media;
CREATE DATABASE admin;
