from __future__ import annotations

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import make_engine, make_session_local, Base, DEFAULT_SQLITE_URL
from . import models, schemas, crud

SQLITE_URL = os.getenv("SQLITE_URL", DEFAULT_SQLITE_URL)
MEDIA_DIR = os.getenv("MEDIA_DIR", "media")

engine = make_engine(SQLITE_URL)
SessionLocal = make_session_local(engine)

# Create tables if missing (simple bootstrap)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dutch Anki Cards API", version="0.1.0")

# Serve extracted mp3
if os.path.isdir(MEDIA_DIR):
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _audio_url(audio: str | None) -> str | None:
    if not audio:
        return None
    return f"/media/{audio}"

@app.get("/cards", response_model=list[schemas.CardOut])
def api_list_cards(q: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    cards = crud.list_cards(db, q=q, limit=limit, offset=offset)
    out = []
    for c in cards:
        item = schemas.CardOut.model_validate(c, from_attributes=True)
        item.audio_url = _audio_url(c.audio)
        out.append(item)
    return out

@app.get("/cards/random", response_model=schemas.CardOut)
def api_random_card(db: Session = Depends(get_db)):
    c = crud.random_card(db)
    if not c:
        raise HTTPException(status_code=404, detail="No cards in database")
    item = schemas.CardOut.model_validate(c, from_attributes=True)
    item.audio_url = _audio_url(c.audio)
    return item

@app.get("/cards/{card_id}", response_model=schemas.CardOut)
def api_get_card(card_id: int, db: Session = Depends(get_db)):
    c = crud.get_card(db, card_id)
    if not c:
        raise HTTPException(status_code=404, detail="Card not found")
    item = schemas.CardOut.model_validate(c, from_attributes=True)
    item.audio_url = _audio_url(c.audio)
    return item
