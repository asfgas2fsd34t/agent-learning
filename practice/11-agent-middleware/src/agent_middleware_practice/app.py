import os
import sys
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain.tools import tool
from langchain_openai import ChatOpenAI


def authorize_region(user_id: str, region: str) -> bool:
    permissions = {"user_1": {"华东"}, "admin": {"华东", "华南"}}
    return region in permissions.get(user_id, set())


def create_query_tool(user_id: str):
    @tool
    def query_sales(month: str, region: str) -> dict[str, Any]:
        """查询月份和区域销售额。"""
        if not authorize_region(user_id, region):
            return {"success": False, "error_code": "FORBIDDEN", "retryable": False}
        return {"success": True, "month": month, "region": region, "amount": 128000.0}
    return query_sales


def create_model() -> ChatOpenAI:
    options: dict[str, Any] = {"model": os.environ["LLM_MODEL"], "api_key": os.environ["LLM_API_KEY"], "temperature": 0}
    if os.getenv("LLM_BASE_URL"):
        options["base_url"] = os.environ["LLM_BASE_URL"]
    return ChatOpenAI(**options)


def build_agent(model: Any, user_id: str):
    sales_tool = create_query_tool(user_id)
    return create_agent(
        model=model,
        tools=[sales_tool],
        system_prompt="需要销售数据时调用工具。权限失败后不要重试。",
        middleware=[ModelCallLimitMiddleware(run_limit=5), ToolCallLimitMiddleware(tool_name=sales_tool.name, run_limit=2)],
    )


def main() -> None:
    load_dotenv()
    question = " ".join(sys.argv[1:]).strip() or input("问题：").strip()
    result = build_agent(create_model(), "user_1").invoke({"messages": [{"role": "user", "content": question}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()

