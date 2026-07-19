# 03 LangChain Tools

## 学习目标

这一课把原生 Tool Calling 映射到 LangChain v1。重点不是重新学习工具调用原理，而是理解框架如何从 Python 函数生成工具 Schema、绑定模型并把 `tool_calls` 转换成真实函数调用。

## 核心流程

```text
Python 函数 + 类型标注 + docstring
-> @tool 生成 BaseTool
-> bind_tools() 把 Schema 交给模型
-> AIMessage.tool_calls
-> 应用代码校验并执行工具
-> ToolMessage 返回模型
```

## `@tool`

```python
from langchain.tools import tool


@tool
def query_sales(month: str, region: str) -> dict:
    """查询指定月份和区域的销售额。"""
    ...
```

LangChain 会读取函数名、docstring、参数名和类型标注生成 JSON Schema。docstring 是给模型看的工具说明，不是业务权限。

可以检查：

```python
query_sales.name
query_sales.description
query_sales.args_schema.model_json_schema()
```

## 工具调用与工具执行

```python
model_with_tools = model.bind_tools([query_sales])
message = model_with_tools.invoke(messages)
```

如果模型选择工具，结果位于：

```python
message.tool_calls
```

典型结构：

```python
{
    "id": "call_1",
    "name": "query_sales",
    "args": {"month": "2026-06", "region": "华东"},
}
```

模型只提出调用请求，真正执行仍由应用代码完成：

```python
result = query_sales.invoke(tool_call["args"])
```

## ToolMessage

工具结果要带上原始 `tool_call_id`：

```python
from langchain.messages import ToolMessage

ToolMessage(
    content=json.dumps(result, ensure_ascii=False),
    tool_call_id=tool_call["id"],
)
```

它让模型知道这个结果对应哪一次工具调用。

## 错误协议

工具不要只返回模糊字符串。推荐统一字段：

```json
{
  "success": false,
  "error_code": "INVALID_MONTH",
  "message": "月份格式必须是 YYYY-MM",
  "retryable": false
}
```

模型可以根据 `retryable` 判断是否值得调整参数，但业务代码仍要限制调用次数。

## 生产边界

- 模型生成的参数是不可信输入，工具入口必须再次校验。
- 查询权限必须根据服务端身份上下文判断，不能让模型传 `can_query=true`。
- 写工具必须具备业务幂等键、状态机和人工确认。
- 工具异常要转换成稳定错误协议，不能把堆栈直接发给模型。
- Tool Calling 不等于 Agent；只有形成“推理、执行、观察、继续”的循环才是 Agent。

## 对应实践

[practice/07-langchain-tools](../../practice/07-langchain-tools/README.md) 使用 `@tool` 定义销售查询工具，完成一次真实的模型选工具、应用执行、`ToolMessage` 回传和最终回答。

## 自测

1. `@tool` 从哪些信息生成 Schema？
2. 为什么模型不能直接执行 Python 函数？
3. `tool_call_id` 有什么作用？
4. 为什么工具参数仍需业务校验？
5. Tool Calling 和 Agent 的区别是什么？

## 官方资料

- [Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [Tool Calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling)

