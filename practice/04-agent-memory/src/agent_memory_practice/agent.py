from typing import Any

from .config import Settings
from .memory import Message, SQLiteConversationMemory


SYSTEM_PROMPT = "你是一名简洁、准确的 Agent 开发助手。"


def answer_question(
    conversation_id: str,
    question: str,
    settings: Settings,
    memory: SQLiteConversationMemory,
    *,
    client: Any | None = None,
    history_limit: int = 20,
) -> str:
    if client is None:
        from openai import OpenAI

        options: dict[str, str] = {"api_key": settings.api_key}
        if settings.base_url:
            options["base_url"] = settings.base_url
        client = OpenAI(**options)

    history = memory.load_recent(conversation_id, limit=history_limit)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *[
            {"role": message.role, "content": message.content}
            for message in history
        ],
        {"role": "user", "content": question},
    ]

    response = client.chat.completions.create(
        model=settings.model,
        messages=messages,
    )
    answer = response.choices[0].message.content
    if not answer:
        raise ValueError("模型返回了空内容")

    memory.append(conversation_id, Message("user", question))
    memory.append(conversation_id, Message("assistant", answer))
    return answer
