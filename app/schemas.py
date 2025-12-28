from __future__ import annotations

from pydantic import BaseModel

class CardOut(BaseModel):
    id: int
    rank: str | None = None
    word: str | None = None
    pos: str | None = None
    definition: str | None = None
    dutch: str | None = None
    english: str | None = None
    ru: str    | None = None# 👈 NEW
    ukr:str  | None = None  # 👈 NEW
    freq: float | None = None
    audio: str | None = None
    audio_url: str | None = None

    model_config = {"from_attributes": True}
