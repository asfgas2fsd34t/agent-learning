# Agent 循环代码速查表

## 最小循环结构

```python
MAX_STEPS = 5

for step in range(MAX_STEPS):
    response = call_model(messages)

    if not response.tool_calls:
        return response.content

    messages.append(response.as_assistant_message())

    for tool_call in response.tool_calls:
        result = execute_tool(tool_call)
        messages.append(as_tool_message(tool_call.id, result))

return "任务执行步骤超过上限，已停止。"
```

## 每轮状态

```text
messages
├── system：Agent 规则
├── user：用户目标
├── assistant：模型的工具选择
├── tool：工具执行结果
└── assistant：下一轮决策或最终回答
```

## 必须保护的边界

- 最大执行步骤
- 单工具最大调用次数
- 总超时时间
- 重复工具和参数检测
- 写操作幂等键
- 权限校验和人工确认
