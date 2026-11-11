"""SQLAlchemy engine, session setup, and helper functions."""

import hashlib
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Resolve the database path relative to the project root (brew-talk/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "cafe.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_menu_version(db: Session | None = None) -> str:
    """
    Return a hash of all menu items (id, name, price, available, updated_at).
    Used for ETag-style polling so the frontend knows when to refresh.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        rows = db.execute(
            text("SELECT id, name, price, available, updated_at FROM menu_items ORDER BY id")
        ).fetchall()
        raw = "|".join(
            f"{r[0]}:{r[1]}:{r[2]}:{r[3]}:{r[4]}" for r in rows
        )
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    finally:
        if close_db:
            db.close()


def get_settings_version(db: Session | None = None) -> str:
    """Return a hash of all settings (key, value). Used for polling."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        rows = db.execute(
            text("SELECT key, value FROM settings ORDER BY key")
        ).fetchall()
        raw = "|".join(f"{r[0]}:{r[1]}" for r in rows)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()
    finally:
        if close_db:
            db.close()
