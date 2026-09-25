from sqlalchemy import inspect, text

from core.db import engine, ensure_added_columns


def test_old_trips_table_gets_new_columns(client):
    # Таблица, какой она была на развёрнутом стенде до отмены выездов.
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE volunteer_trips"))
        conn.execute(
            text(
                "CREATE TABLE volunteer_trips (id VARCHAR(36) PRIMARY KEY, squad_id VARCHAR(36), "
                "title VARCHAR(255), created_at DATETIME)"
            )
        )
        conn.execute(text("INSERT INTO volunteer_trips (id, squad_id, title) VALUES ('t1', 's1', 'Старый выезд')"))

    ensure_added_columns(engine)
    ensure_added_columns(engine)  # повторный запуск сервиса ничего не ломает

    columns = {column["name"] for column in inspect(engine).get_columns("volunteer_trips")}
    assert {"status", "cancel_reason"} <= columns
    with engine.connect() as conn:
        status, reason = conn.execute(text("SELECT status, cancel_reason FROM volunteer_trips")).one()
    assert (status, reason) == ("planned", "")
