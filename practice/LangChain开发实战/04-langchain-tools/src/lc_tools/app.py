import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI


SALES = {
    ("2026-06", "华东"): 128000.0,
    ("2026-06", "华南"): 96000.0,
}


@tool
def query_sales(month: str, region: str) -> dict[str, Any]:
    """查询指定月份和区域的销售额；月份格式必须为 YYYY-MM。"""
    if len(month) != 7 or month[4] != "-":
        return {"success": False, "error_code": "INVALID_MONTH", "message": "月份格式必须为 YYYY-MM", "retryable": False}
    amount = SALES.get((month, region))
    if amount is None:
        return {"success": False, "error_code": "NO_DATA", "message": "没有找到销售数据", "retryable": False}
    return {"success": True, "data": {"month": month, "region": region, "amount": amount}, "message": "查询成功", "retryable": False}


TOOLS = {query_sales.name: query_sales}


def create_model() -> ChatOpenAI:
    options: dict[str, Any] = {
        "model": os.environ["LLM_MODEL"],
        "api_key": os.environ["LLM_API_KEY"],
        "temperature": 0,
    }
    if os.getenv("LLM_BASE_URL"):
        options["base_url"] = os.environ["LLM_BASE_URL"]
    return ChatOpenAI(**options)


def run_tool_conversation(question: str, model: Any) -> str:
    bound_model = model.bind_tools(list(TOOLS.values()))
    messages = [
        SystemMessage("你是销售助手。需要真实销售数据时必须调用工具，不得编造。"),
        HumanMessage(question),
    ]
    first = bound_model.invoke(messages)
    messages.append(first)
    for call in first.tool_calls:
        selected = TOOLS.get(call["name"])
        result = selected.invoke(call["args"]) if selected else {"success": False, "error_code": "UNKNOWN_TOOL", "retryable": False}
        messages.append(ToolMessage(json.dumps(result, ensure_ascii=False), tool_call_id=call["id"]))
    if not first.tool_calls:
        return str(first.content)
    final = bound_model.invoke(messages)
    return str(final.content)


def main() -> None:
    load_dotenv()
    question = " ".join(sys.argv[1:]).strip() or input("问题：").strip()
    print(run_tool_conversation(question, create_model()))


if __name__ == "__main__":
    main()

