from __future__ import annotations

import os
import json
import logging

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from openai import OpenAI

from app.database import SessionLocal
from app.models import Card

# ---------- config ----------
BATCH_SIZE = 20
MODEL = "gpt-4.1-mini"   # дешёвый и стабильный
# ----------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "autofill_ru_ukr.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),  # ← можно убрать, если не хочешь вывод в терминал
    ],
)

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _clean_text(s: str, limit: int = 800) -> str:
    s = (s or "").strip()
    if len(s) > limit:
        s = s[:limit]
    return s

def translate_batch(items: list[tuple[int, str]]) -> dict[int, tuple[str | None, str | None]]:
    """
    items: [(card_id, english_text), ...]
    returns: {card_id: (ru, ukr), ...}
    """
    # готовим компактный список для модели
    payload = [{"id": cid, "en": _clean_text(en)} for cid, en in items if _clean_text(en)]
    if not payload:
        return {}

    prompt = (
        "You are a translation engine.\n"
        "Translate each 'en' into Russian (ru) and Ukrainian (ukr).\n"
        "Return ONLY valid JSON (no markdown, no explanations).\n"
        "Keep translations concise. Preserve <br> tags if present.\n\n"
        "Input JSON:\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Output JSON MUST be an array of objects with EXACT keys: id, ru, ukr\n"
        "Example:\n"
        '[{"id": 123, "ru": "...", "ukr": "..."}, {"id": 124, "ru": "...", "ukr": "..."}]'
    )

    try:
        response = client.responses.create(
            model=MODEL,
            input=prompt,
            # батч может быть длиннее
            max_output_tokens=1200,
        )

        raw = response.output_text.strip()
        #print("RAW BATCH OUTPUT:", raw)  # временно для отладки, если надо

        # вырезаем JSON-массив
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == -1:
            raise ValueError(f"No JSON array found in response: {raw[:400]}")

        data = json.loads(raw[start:end])

        out: dict[int, tuple[str | None, str | None]] = {}
        for obj in data:
            try:
                cid = int(obj.get("id"))
            except Exception:
                continue
            ru = (obj.get("ru") or "").strip() or None
            ukr = (obj.get("ukr") or "").strip() or None
            out[cid] = (ru, ukr)

        return out

    except Exception:
        logger.exception("translate_batch error")
    return {}





def main():
    db: Session = SessionLocal()

    cards = db.scalars(
        select(Card)
        .where(
            (Card.english.is_not(None))
            & ((Card.ru.is_(None)) | (Card.ukr.is_(None)))
        )
        .limit(BATCH_SIZE)
    ).all()

    print(f"🔎 found {len(cards)} cards")

    batch_items = [(c.id, c.english or "") for c in cards]
    results = translate_batch(batch_items)

    updated = 0

    for c in cards:
        ru_ukr = results.get(c.id)
        if not ru_ukr:
            logger.warning("SKIP | id=%s | EN=%s", c.id, c.english)
            missing += 1
            continue

        ru, ukr = ru_ukr

        logger.info(
        "CARD %s\nEN: %s\nRU: %s\nUKR: %s\n",
        c.id,
        c.english,
        ru,
        ukr,
        )

        if ru is not None:
            c.ru = ru
        if ukr is not None:
            c.ukr = ukr

        if ru is not None or ukr is not None:
            updated += 1

    db.commit()
    db.close()

    print(f"✅ batch done. updated={updated}/{len(cards)}")   


if __name__ == "__main__":
    main()
