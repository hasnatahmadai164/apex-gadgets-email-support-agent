"""
Database engine & session factory.

The engine and session factory are built lazily (via `lru_cache`)
rather than at import time, so importing this module never requires
`DATABASE_URL` to already be set — Alembic's `env.py` imports
`app.db.models` but builds its own engine, and test modules that only
need the ORM models don't need a live database either.
"""

from collections.abc import Generator

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """Yield a `Session`, closing it afterward.

    Usable as a plain generator (`session = next(get_session())`) or,
    once the dashboard exists, as a FastAPI dependency via `Depends`.
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
