from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DEFAULT_SQLITE_URL = "sqlite:///./cards.db"

class Base(DeclarativeBase):
    pass

def make_engine(sqlite_url: str = DEFAULT_SQLITE_URL):
    # check_same_thread=False is required for SQLite with FastAPI default threadpool
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})

def make_session_local(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)

# ✅ ДОБАВИТЬ ЭТИ СТРОКИ
engine = make_engine()
SessionLocal = make_session_local(engine)