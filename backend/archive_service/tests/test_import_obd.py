"""Импорт погибших из ОБД «Мемориал» в Книгу памяти (scripts/import_obd_fighters.py)."""

import gzip
import json

from core.db import SessionLocal
from scripts import import_obd_fighters as importer

OBD = "https://obd-memorial.ru/html/info.htm?id=89564437"
FIGHTERS = [
    {
        "id": "bc819bd7-491f-5446-bd7f-41657054c653",
        "full_name": "Абабекиров  Усиурзак",
        "birth_year": 1905,
        "death_date": "1943-07-13",
        "rank": "красноармеец",
        "unit": "233 сп 97 сд",
        "burial_place": "Орловская обл., Болховский р-н, д. Пальчиково, братская могила",
        "lat": 53.3,
        "lon": 36.1,
        "source": f"ОБД «Мемориал», поимённый список захоронения, {OBD}",
        "biography": "Год рождения — 1905. Воинское звание — красноармеец.",
    },
    {
        "id": "78f023c4-91da-531a-aeec-ef738072887d",
        "full_name": "Бобров Иван",
        "birth_year": None,
        "death_date": None,
        "lat": None,
        "lon": None,
        "source": "ОБД «Мемориал»",
        "biography": "Пропал без вести.",
    },
    # Без id не импортируем: повторный запуск не нашёл бы, что обновить.
    {"id": "", "full_name": "Без id"},
]


def run(fighters):
    with SessionLocal() as db:
        return importer.import_fighters(db, fighters)


def cards(client):
    response = client.get("/entries", params={"kind": "soldier_card", "sort": "title"})
    assert response.status_code == 200
    return response.json()


def test_fighters_become_verified_soldier_cards(client):
    assert run(FIGHTERS) == 2

    first, second = cards(client)
    assert first["title"] == "Абабекиров Усиурзак"
    assert first["date_text"] == "1905 — 13.07.1943"
    assert first["event_date"] == "1943-07-13"
    assert (first["lat"], first["lon"]) == (53.3, 36.1)
    # Ссылка на анкету — отдельной строкой: веб-архив показывает её кнопкой.
    assert first["body"].endswith(f"Источник: {OBD}")
    assert "Данные: ОБД «Мемориал», поимённый список захоронения." in first["body"]
    assert second["title"] == "Бобров Иван"
    assert second["date_text"] == ""

    summary = client.get("/entries/summary", params={"kind": "soldier_card"}).json()
    assert summary == {"total": 2, "with_date": 1, "on_map": 1, "letters": ["А", "Б"]}


def test_reimport_updates_the_same_cards(client):
    run(FIGHTERS)
    run([dict(FIGHTERS[0], biography="Уточнённая биография.")])

    first, second = cards(client)
    assert first["body"].startswith("Уточнённая биография.")
    assert second["title"] == "Бобров Иван"


def test_reads_gzipped_export(tmp_path):
    path = tmp_path / "fighters.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(FIGHTERS, f, ensure_ascii=False)

    assert len(importer.load(path)) == 3
