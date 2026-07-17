from typing import Any

from .sales import query_sales

SALES_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "query_sales",
        "description": (
            "按指定月份和地区查询销售额，只执行只读查询。"
            "当用户需要获取真实销售额时使用。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "month": {
                    "type": "string",
                    "description": "查询月份，格式为 YYYY-MM，例如 2026-06",
                },
                "region": {
                    "type": "string",
                    "enum": ["华东", "华南", "华北"],
                    "description": "销售地区",
                },
            },
            "required": ["month", "region"],
            "additionalProperties": False,
        },
    },
}

TOOLS = [SALES_TOOL]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name != "query_sales":
        return {
            "success": False,
            "error_code": "UNKNOWN_TOOL",
            "message": f"未知工具：{name}",
            "retryable": False,
        }

    return query_sales(
        month=arguments.get("month", ""),
        region=arguments.get("region", ""),
    )
