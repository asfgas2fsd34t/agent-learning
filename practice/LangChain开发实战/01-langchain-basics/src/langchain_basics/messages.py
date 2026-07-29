from langchain.messages import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage


SYSTEM_PROMPT = "你是一名准确、简洁的 Agent 开发导师。"


def build_chat_messages(question: str) -> list[BaseMessage]:
    question = question.strip()
    if not question:
        raise ValueError("问题不能为空")
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]
