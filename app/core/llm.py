from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

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


def build_embedding_model(deployment: str | None = None) -> AzureOpenAIEmbeddings:
    settings = get_settings()
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=deployment or settings.azure_openai_embedding_deployment,
    )
