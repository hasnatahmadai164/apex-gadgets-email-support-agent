"""
Centralized application configuration.

All runtime configuration is sourced from environment variables (loaded
from a local `.env` file in development, or from real environment
variables / secrets in deployed containers — the Container Apps Job
and the dashboard Container App both get their env vars injected the
same way, so this module doesn't need to know or care which one it's
running in).

Nothing else in the codebase should call `os.environ` directly —
import `get_settings()` instead, so there is exactly one place that
knows how to parse and validate configuration.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    See `.env.example` for the full list of variables and a note on
    which project stage introduces each one. Fields with no default
    are required — the app will fail fast at startup if they're
    missing, rather than failing confusingly later.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # tolerate unrelated vars in the environment
    )

    # --- Postgres ---------------------------------------------------------
    database_url: str = Field(..., alias="DATABASE_URL")

    # --- Azure OpenAI / Foundry — chat models ------------------------------
    azure_openai_endpoint: str | None = Field(None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field("2024-10-21", alias="AZURE_OPENAI_API_VERSION")

    azure_openai_relevance_deployment: str = Field(
        "gpt-4o-mini", alias="AZURE_OPENAI_RELEVANCE_DEPLOYMENT"
    )
    azure_openai_sensitivity_deployment: str = Field(
        "gpt-4o-mini", alias="AZURE_OPENAI_SENSITIVITY_DEPLOYMENT"
    )
    azure_openai_specialist_deployment: str = Field(
        "gpt-5-mini", alias="AZURE_OPENAI_SPECIALIST_DEPLOYMENT"
    )

    # --- Azure OpenAI — embeddings -------------------------------------------
    azure_openai_embedding_deployment: str = Field(
        "text-embedding-3-small", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )

    # --- Pinecone --------------------------------------------------------------
    pinecone_api_key: str | None = Field(None, alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field("apex-gadgets-db", alias="PINECONE_INDEX_NAME")

    # --- Gmail OAuth --------------------------------------------------------------
    gmail_client_id: str | None = Field(None, alias="GMAIL_CLIENT_ID")
    gmail_client_secret: str | None = Field(None, alias="GMAIL_CLIENT_SECRET")
    gmail_refresh_token: str | None = Field(None, alias="GMAIL_REFRESH_TOKEN")
    gmail_support_address: str | None = Field(None, alias="GMAIL_SUPPORT_ADDRESS")

    # --- Dashboard -------------------------------------------------------------------
    dashboard_admin_username: str = Field("admin", alias="DASHBOARD_ADMIN_USERNAME")
    dashboard_admin_password: str | None = Field(None, alias="DASHBOARD_ADMIN_PASSWORD")

    # --- App ---------------------------------------------------------------------------
    environment: str = Field("local", alias="ENVIRONMENT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance.

    Both long-lived processes in this project (the poller inside its
    Container Apps Job run, and the dashboard's HTTP server) want to
    read `.env` / the environment exactly once and then reuse the
    parsed result — not re-parse it on every call site.
    """
    return Settings()
