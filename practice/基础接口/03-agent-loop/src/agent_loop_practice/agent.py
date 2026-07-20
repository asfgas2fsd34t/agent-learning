import json
from typing import Any

from .config import Settings
from .tools import TOOLS, execute_tool, tool_call_signature


SYSTEM_PROMPT = (
    "你是销售数据助手。需要真实销售数据时必须调用工具，不能编造数据。"
    "工具返回错误时不要重复调用相同工具和参数。"
)


def answer_question(
    question: str,
    settings: Settings,
    *,
    client: Any | None = None,
    max_steps: int = 5,
    max_same_call: int = 2,
) -> str:
    if max_steps < 1 or max_same_call < 1:
        raise ValueError("max_steps 和 max_same_call 必须大于 0")

    if client is None:
        from openai import OpenAI

        options: dict[str, str] = {"api_key": settings.api_key}
        if settings.base_url:
            options["base_url"] = settings.base_url
        client = OpenAI(**options)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    call_counts: dict[str, int] = {}

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        assistant = response.choices[0].message

        if not assistant.tool_calls:
            if not assistant.content:
                raise ValueError("模型没有生成最终回答")
            return assistant.content

        serialized_calls = []
        for tool_call in assistant.tool_calls:
            serialized_calls.append(
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            )

        messages.append(
            {
                "role": "assistant",
                "content": assistant.content,
                "tool_calls": serialized_calls,
            }
        )

        for tool_call in assistant.tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                result = {
                    "success": False,
                    "error_code": "INVALID_ARGUMENTS",
                    "message": "工具参数不是合法 JSON",
                    "retryable": False,
                }
            else:
                signature = tool_call_signature(tool_call.function.name, arguments)
                call_counts[signature] = call_counts.get(signature, 0) + 1

                if call_counts[signature] > max_same_call:
                    result = {
                        "success": False,
                        "error_code": "DUPLICATE_TOOL_CALL",
                        "message": "相同工具和参数超过调用上限",
                        "retryable": False,
                    }
                else:
                    result = execute_tool(tool_call.function.name, arguments)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError("Agent 执行步骤超过上限")
