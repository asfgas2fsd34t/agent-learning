from typing import Any

from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)


def normalize_text(value: dict[str, str]) -> str:
    text = value.get("text", "")
    normalized = " ".join(text.strip().split())
    if not normalized:
        raise ValueError("文本不能为空")
    return normalized


def text_length(value: dict[str, str]) -> int:
    return len(normalize_text(value))


def merge_features(value: dict[str, Any]) -> dict[str, Any]:
    features = value["features"]
    original = {
        key: item
        for key, item in value.items()
        if key != "features"
    }
    return {**original, **features}


def create_preparation_chain() -> Runnable[dict[str, str], dict[str, Any]]:
    feature_runnables = RunnableParallel(
        normalized_text=RunnableLambda(normalize_text),
        text_length=RunnableLambda(text_length),
    )
    return (
        RunnablePassthrough.assign(features=feature_runnables)
        | RunnableLambda(merge_features)
    )
