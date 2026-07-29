from typing import Any

from langchain_core.runnables import Runnable, RunnableLambda


def build_chain() -> Runnable[Any, str]:
    """构建一个本地可测试的 Runnable 链，不依赖模型或网络。"""
    return RunnableLambda(lambda value: value["question"].strip()) | RunnableLambda(
        lambda question: f"收到问题：{question}"
    )


def build_trace_config(request_id: str, environment: str = "local") -> dict[str, Any]:
    """构造可观测性配置；metadata 只放脱敏后的关联信息。"""
    return {
        "run_name": "langsmith_learning_chain",
        "tags": ["agent-learning", "runnable", environment],
        "metadata": {
            "request_id": request_id,
            "environment": environment,
        },
    }


def invoke_observed(
    question: str,
    *,
    request_id: str,
    environment: str = "local",
) -> str:
    chain = build_chain()
    result = chain.invoke(
        {"question": question},
        config=build_trace_config(request_id, environment),
    )
    return str(result)
