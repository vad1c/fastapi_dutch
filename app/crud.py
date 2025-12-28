from __future__ import annotations

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from .models import Card

def get_card(db: Session, card_id: int) -> Card | None:
    return db.get(Card, card_id)

def list_cards(db: Session, q: str | None = None, limit: int = 50, offset: int = 0) -> list[Card]:
    stmt = select(Card)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Card.word.ilike(like),
                Card.dutch.ilike(like),
                Card.english.ilike(like),
                Card.definition.ilike(like),
            )
        )
    stmt = stmt.order_by(Card.id).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars())

def random_card(db: Session) -> Card | None:
    stmt = select(Card).order_by(func.random()).limit(1)
    return db.execute(stmt).scalars().first()
