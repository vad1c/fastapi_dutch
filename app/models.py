from __future__ import annotations

from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    rank: Mapped[str | None] = mapped_column(String, nullable=True)
    word: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    pos: Mapped[str | None] = mapped_column(String, nullable=True)
    definition: Mapped[str | None] = mapped_column(String, nullable=True)

    dutch: Mapped[str | None] = mapped_column(String, nullable=True)
    english: Mapped[str | None] = mapped_column(String, nullable=True)
    ru: Mapped[str | None] = mapped_column(String, nullable=True)   # ✅ NEW
    ukr: Mapped[str | None] = mapped_column(String, nullable=True)  # ✅ NEW


    freq: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
