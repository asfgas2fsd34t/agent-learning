import json
from typing import Any

from .config import Settings
from .tools import TOOLS, execute_tool

SYSTEM_PROMPT = (
    "你是一个销售数据助手。涉及真实销售额时必须使用工具，"
    "不能编造数据。请根据工具结果用简洁中文回答。"
)


def answer_question(
    question: str,
    settings: Settings,
    *,
    client: Any | None = None,
    max_steps: int = 5,
    max_same_call: int = 2,
) -> str:
    if max_steps < 1:
        raise ValueError("max_steps 必须大于 0")
    if max_same_call < 1:
        raise ValueError("max_same_call 必须大于 0")

    if client is None:
        from openai import OpenAI

        client_options: dict[str, str] = {"api_key": settings.api_key}
        if settings.base_url:
            client_options["base_url"] = settings.base_url
        client = OpenAI(**client_options)

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
        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls

        if not tool_calls:
            if not assistant_message.content:
                raise ValueError("模型既没有回答，也没有请求工具")
            return assistant_message.content

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ],
            }
        )

        for tool_call in tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_result = {
                    "success": False,
                    "error_code": "INVALID_ARGUMENTS",
                    "message": "工具参数不是合法 JSON",
                    "retryable": False,
                }
            else:
                signature = (
                    f"{tool_call.function.name}:"
                    f"{json.dumps(arguments, sort_keys=True, ensure_ascii=False)}"
                )
                call_counts[signature] = call_counts.get(signature, 0) + 1

                if call_counts[signature] > max_same_call:
                    tool_result = {
                        "success": False,
                        "error_code": "DUPLICATE_TOOL_CALL",
                        "message": "相同工具和参数已达到重复调用上限",
                        "retryable": False,
                    }
                else:
                    tool_result = execute_tool(tool_call.function.name, arguments)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    raise RuntimeError("Agent 执行步骤超过上限")
