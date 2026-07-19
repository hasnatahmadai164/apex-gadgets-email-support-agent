import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_reads_database_url_from_env():
    settings = get_settings()
    assert settings.database_url == "postgresql+psycopg2://test:test@localhost:5432/test"


def test_settings_has_sensible_defaults_for_deployment_names():
    settings = get_settings()
    assert settings.azure_openai_relevance_deployment == "gpt-5-mini"
    assert settings.azure_openai_sensitivity_deployment == "gpt-5-mini"
    assert settings.azure_openai_specialist_deployment == "gpt-5-mini"
    assert settings.azure_openai_embedding_deployment == "text-embedding-3-small"


def test_settings_defaults_pinecone_index_name():
    settings = get_settings()
    assert settings.pinecone_index_name == "apex-gadgets-db"


def test_settings_is_cached_across_calls():
    # Same object identity — proves the lru_cache is actually caching,
    # not just returning equal-but-distinct instances.
    assert get_settings() is get_settings()


def test_missing_database_url_raises_validation_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
