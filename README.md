# FastAPI + SQLite + SQLAlchemy каркас для Anki-колоды (APKG)

## Что внутри
- FastAPI API для карточек.
- SQLite база `cards.db`
- SQLAlchemy 2.0 ORM (синхронный движок — проще стартовать).
- Скрипт импорта `app/import_anki.py`, который:
  - читает `.apkg`
  - парсит поля нот: Rank, Word, Part-of-Speech, Definition, Dutch, English, Freq, Word Audio
  - сохраняет в SQLite
  - извлекает mp3 из APKG в папку `media/` (по имени файла из Anki)

## Быстрый старт
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt

# Импорт из APKG (укажи путь к файлу)
python -m app.import_anki --apkg /path/to/A_Frequency_Dictionary_of_Dutch.apkg --db cards.db --media-dir media

# Запуск API
uvicorn app.main:app --reload
```

Открой: `http://127.0.0.1:8000/docs`

## API
- `GET /cards` — список (параметры: `q`, `limit`, `offset`)
- `GET /cards/{id}` — по id
- `GET /cards/random` — случайная карточка
- `GET /media/{filename}` — раздача mp3 (если был извлечён)

## Примечания
- Поле `audio` в базе хранит имя файла, например `Nl-de.mp3` (или `null`, если аудио нет).
- В Anki аудио обычно лежит как `[sound:NAME.mp3]` — скрипт автоматически вытаскивает `NAME.mp3`.
