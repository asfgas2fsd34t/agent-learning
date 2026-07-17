from typing import Any

from .config import Settings

SYSTEM_PROMPT = "你是一名耐心、准确的 Agent 开发导师。"


def ask_model(
    question: str,
    settings: Settings,
    *,
    client: Any | None = None,
) -> str:
    if client is None:
        from openai import OpenAI

        client_options: dict[str, str] = {"api_key": settings.api_key}
        if settings.base_url:
            client_options["base_url"] = settings.base_url
        client = OpenAI(**client_options)

    response = client.chat.completions.create(
        model=settings.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("模型返回了空内容")
    return content
