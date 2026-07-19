from langchain_openai import ChatOpenAI

from .config import Settings


def create_chat_model(settings: Settings) -> ChatOpenAI:
    options: dict[str, object] = {
        "model": settings.model,
        "api_key": settings.api_key,
        "temperature": 0,
    }
    if settings.base_url:
        options["base_url"] = settings.base_url
    return ChatOpenAI(**options)

