from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableBranch

from .runnables import create_preparation_chain


SHORT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是学习助手。只根据输入内容，用三个短要点总结。",
        ),
        ("human", "请总结：\n{normalized_text}"),
    ]
)

LONG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是学习助手。只根据输入内容总结，先提炼主题，再整理关键概念和它们之间的关系。",
        ),
        ("human", "请详细总结下面内容，并保留重要的因果关系：\n{normalized_text}"),
    ]
)


def create_adaptive_summary_chain(
    model: Runnable[Any, Any],
) -> Runnable[dict[str, str], str]:
    short_chain = SHORT_PROMPT | model | StrOutputParser()
    long_chain = LONG_PROMPT | model | StrOutputParser()
    branch = RunnableBranch(
        (lambda value: value["text_length"] > 80, long_chain),
        short_chain,
    )
    return create_preparation_chain() | branch

