import os
import sys
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI


SALES = {("2026-06", "华东"): 128000.0, ("2026-06", "华南"): 96000.0}


@tool
def query_sales(month: str, region: str) -> dict[str, Any]:
    """查询指定月份和区域的销售额。"""
    amount = SALES.get((month, region))
    if amount is None:
        return {"success": False, "error_code": "NO_DATA", "retryable": False}
    return {"success": True, "month": month, "region": region, "amount": amount}


def create_model() -> ChatOpenAI:
    options: dict[str, Any] = {"model": os.environ["LLM_MODEL"], "api_key": os.environ["LLM_API_KEY"], "temperature": 0}
    if os.getenv("LLM_BASE_URL"):
        options["base_url"] = os.environ["LLM_BASE_URL"]
    return ChatOpenAI(**options)


def build_agent(model: Any):
    return create_agent(model=model, tools=[query_sales], system_prompt="你是销售分析助手。涉及销售数据必须调用工具；无数据时明确说明，不得编造。")


def main() -> None:
    load_dotenv()
    question = " ".join(sys.argv[1:]).strip() or input("问题：").strip()
    result = build_agent(create_model()).invoke({"messages": [{"role": "user", "content": question}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()

