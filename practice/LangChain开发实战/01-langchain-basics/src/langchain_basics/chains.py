from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是 Agent 开发导师。只根据用户提供的内容总结，不补充未经提供的事实。",
        ),
        (
            "human",
            "请将下面的学习内容总结为三个要点，最后给出一句话总结：\n\n{text}",
        ),
    ]
)


def create_summary_chain(model: Runnable[Any, Any]) -> Runnable[dict[str, str], str]:
    return SUMMARY_PROMPT | model | StrOutputParser()


def summarize_text(text: str, model: Runnable[Any, Any]) -> str:
    text = text.strip()
    if not text:
        raise ValueError("待总结内容不能为空")
    return create_summary_chain(model).invoke({"text": text})

