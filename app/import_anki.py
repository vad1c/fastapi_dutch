from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import zipfile
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .database import Base
from .models import Card

SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")

def extract_audio_field(value: str | None) -> str | None:
    if not value:
        return None
    m = SOUND_RE.search(value)
    if m:
        return m.group(1).strip()
    # sometimes it's already a filename
    v = value.strip()
    if v.lower().endswith(".mp3"):
        return v
    return None

def parse_freq(value: str | None) -> float | None:
    if not value:
        return None
    v = value.strip().replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None

def import_apkg(apkg_path: Path, db_path: Path, media_dir: Path):
    media_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(apkg_path) as zf:
        # pick modern collection
        collection_name = "collection.anki21" if "collection.anki21" in zf.namelist() else "collection.anki2"
        collection_bytes = zf.read(collection_name)

        tmp_collection = media_dir.parent / "_collection_tmp.sqlite"
        tmp_collection.write_bytes(collection_bytes)

        # media mapping: {"1234":"Nl-de.mp3", ...}
        media_map = json.loads(zf.read("media").decode("utf-8")) if "media" in zf.namelist() else {}

        # open anki sqlite
        conn = sqlite3.connect(tmp_collection)
        cur = conn.cursor()

        # model fields order from notes.flds (\x1f) is defined by model in col.models,
        # but in this deck it's exactly the 8 fields we need.
        cur.execute("SELECT id, flds FROM notes")
        notes = cur.fetchall()

        sqlite_url = f"sqlite:///{db_path}"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

        Base.metadata.create_all(bind=engine)

        # clean table for idempotent imports (optional)
        with Session(engine) as session:
            session.query(Card).delete()
            session.commit()

            batch = []
            for _nid, flds in notes:
                parts = (flds or "").split("\x1f")
                # pad in case of weird rows
                while len(parts) < 8:
                    parts.append("")
                rank, word, pos, definition, dutch, english, freq_s, audio_s = parts[:8]

                audio_name = extract_audio_field(audio_s)
                freq = parse_freq(freq_s)

                card = Card(
                    rank=rank or None,
                    word=word or None,
                    pos=pos or None,
                    definition=definition or None,
                    dutch=dutch or None,
                    english=english or None,
                    freq=freq,
                    audio=audio_name,
                )
                batch.append(card)

                if len(batch) >= 1000:
                    session.add_all(batch)
                    session.commit()
                    batch.clear()

            if batch:
                session.add_all(batch)
                session.commit()

        # Extract mp3 files (only those referenced by the deck)
        # In APKG, files are stored by numeric key; map to real filename.
        extracted = 0
        for num_key, filename in media_map.items():
            if not filename.lower().endswith(".mp3"):
                continue
            # only extract if used by some card OR just extract all mp3 (simple).
            try:
                data = zf.read(num_key)
            except KeyError:
                continue
            out_path = media_dir / filename
            if not out_path.exists():
                out_path.write_bytes(data)
                extracted += 1

        # cleanup temp collection
        try:
            tmp_collection.unlink()
        except OSError:
            pass

        return len(notes), extracted

def main():
    p = argparse.ArgumentParser(description="Import Anki APKG to SQLite (SQLAlchemy) and extract MP3.")
    p.add_argument("--apkg", required=True, help="Path to .apkg file")
    p.add_argument("--db", default="cards.db", help="SQLite db file (default: cards.db)")
    p.add_argument("--media-dir", default="media", help="Directory to extract mp3 (default: media)")
    args = p.parse_args()

    apkg_path = Path(args.apkg).expanduser().resolve()
    db_path = Path(args.db).expanduser().resolve()
    media_dir = Path(args.media_dir).expanduser().resolve()

    count, extracted = import_apkg(apkg_path, db_path, media_dir)
    print(f"Imported {count} notes into {db_path}")
    print(f"Extracted {extracted} mp3 files into {media_dir}")

if __name__ == "__main__":
    main()
