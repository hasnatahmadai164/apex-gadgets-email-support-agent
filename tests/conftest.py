"""
Shared pytest fixtures.

`get_settings()` is `lru_cache`d in application code (deliberately —
see app/core/config.py), which means it needs to be reset between
tests, or a value set by one test leaks into the next. These fixtures
handle that automatically so individual test files don't have to.
"""

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _default_database_url(monkeypatch):
    """Every test gets a valid DATABASE_URL unless it overrides it
    itself — keeps tests that don't care about config from failing
    just because .env isn't present (e.g., in CI).
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://test:test@localhost:5432/test")
