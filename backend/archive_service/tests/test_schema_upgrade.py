from sqlalchemy import inspect, text

from core.db import engine, ensure_added_columns


def test_old_entries_table_gets_link_columns(client):
    # Таблица, какой она была на развёрнутом стенде до связи записи с точкой.
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE archive_entries"))
        conn.execute(
            text("CREATE TABLE archive_entries (id VARCHAR(36) PRIMARY KEY, title VARCHAR(255))")
        )

    ensure_added_columns(engine)
    ensure_added_columns(engine)  # повторный запуск сервиса ничего не ломает

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("archive_entries")}
    assert {"point_id", "poi_id"} <= columns
    indexes = {index["name"] for index in inspector.get_indexes("archive_entries")}
    assert {"ix_archive_entries_point_id", "ix_archive_entries_poi_id"} <= indexes
