from langchain_openai import AzureChatOpenAI

from app.core.config import get_settings
from app.core.llm import build_chat_model


def test_build_chat_model_returns_azure_chat_model(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    model = build_chat_model("gpt-4o-mini")

    assert isinstance(model, AzureChatOpenAI)
