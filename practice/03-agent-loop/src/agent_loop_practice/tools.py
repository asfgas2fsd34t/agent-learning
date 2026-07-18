import json
from typing import Any

from .sales import query_sales


SALES_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "query_sales",
        "description": "按月份和地区查询销售额，只执行只读查询。",
        "parameters": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "YYYY-MM"},
                "region": {
                    "type": "string",
                    "enum": ["华东", "华南", "华北"],
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
        month=str(arguments.get("month", "")),
        region=str(arguments.get("region", "")),
    )


def tool_call_signature(name: str, arguments: dict[str, Any]) -> str:
    return f"{name}:{json.dumps(arguments, sort_keys=True, ensure_ascii=False)}"
