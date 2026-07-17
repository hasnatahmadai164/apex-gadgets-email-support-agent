from langchain_openai import AzureChatOpenAI

from app.core.config import get_settings


def build_chat_model(deployment: str, temperature: float = 0) -> AzureChatOpenAI:
    settings = get_settings()
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=deployment,
        temperature=temperature,
    )
