from typing import Any, Protocol

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field


class StudyNote(BaseModel):
    topic: str = Field(description="学习内容的主题")
    key_points: list[str] = Field(description="三个关键知识点")
    summary: str = Field(description="一句话总结")


class SupportsStructuredOutput(Protocol):
    def with_structured_output(
        self,
        schema: type[BaseModel],
        **kwargs: Any,
    ) -> Runnable[Any, Any]: ...


STUDY_NOTE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是 Agent 开发导师。只提取输入中明确存在的信息，不确定时不要补充。",
        ),
        ("human", "请把下面内容整理成学习笔记：\n\n{text}"),
    ]
)


def create_study_note_chain(
    model: SupportsStructuredOutput,
) -> Runnable[dict[str, str], StudyNote]:
    structured_model = model.with_structured_output(
        StudyNote,
        method="function_calling",
    )
    return STUDY_NOTE_PROMPT | structured_model


def extract_study_note(text: str, model: SupportsStructuredOutput) -> StudyNote:
    text = text.strip()
    if not text:
        raise ValueError("待整理内容不能为空")
    return create_study_note_chain(model).invoke({"text": text})

