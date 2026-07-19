import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver


def conversation_config(thread_id: str) -> dict[str, dict[str, str]]:
    thread_id = thread_id.strip()
    if not thread_id:
        raise ValueError("thread_id 不能为空")
    return {"configurable": {"thread_id": thread_id}}


def create_model() -> ChatOpenAI:
    options: dict[str, Any] = {"model": os.environ["LLM_MODEL"], "api_key": os.environ["LLM_API_KEY"], "temperature": 0}
    if os.getenv("LLM_BASE_URL"):
        options["base_url"] = os.environ["LLM_BASE_URL"]
    return ChatOpenAI(**options)


def build_agent(model: Any, checkpointer: Any | None = None):
    return create_agent(
        model=model,
        tools=[],
        system_prompt="你是简洁的学习助手。只根据当前会话已有信息回答。",
        checkpointer=checkpointer or InMemorySaver(),
    )


def main() -> None:
    load_dotenv()
    agent = build_agent(create_model())
    thread_id = input("会话 ID：").strip() or "default"
    config = conversation_config(thread_id)
    while True:
        question = input("你：").strip()
        if question.lower() in {"exit", "quit", "退出"}:
            return
        if question:
            result = agent.invoke({"messages": [{"role": "user", "content": question}]}, config=config)
            print(f"助手：{result['messages'][-1].content}")


if __name__ == "__main__":
    main()

