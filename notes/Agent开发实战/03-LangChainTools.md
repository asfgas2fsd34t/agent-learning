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

## 深入：`@tool` 到底生成了什么

`@tool` 不是简单给函数加一个标签。它会把普通 Python 函数包装成 LangChain 的工具对象，工具对象同时包含：

```text
name          模型看到的工具名
description   模型看到的使用说明
args_schema   参数校验模型
invoke        应用程序执行工具的入口
```

可以观察：

```python
print(query_sales.name)
print(query_sales.description)
print(query_sales.args_schema.model_json_schema())
```

函数签名和 docstring 会影响模型能否正确调用，但它们不是安全边界：

```text
类型标注 -> 参数 Schema
docstring -> 工具说明
函数体 -> 真实执行逻辑
```

### 参数 Schema 与业务校验是两层

`args_schema` 可以检查：

```text
month 是否为字符串
region 是否存在
必填字段是否缺失
```

但它通常不知道：

```text
用户是否有权查询该 region
月份是否允许查询未来数据
当前订单是否处于可操作状态
金额是否超过业务上限
```

因此工具入口至少有两层校验：

```text
LangChain Schema 校验：结构和类型
业务服务校验：权限、状态、范围、幂等和真实性
```

## 深入：`bind_tools()` 做了什么

```python
bound_model = model.bind_tools([query_sales])
```

它不会执行 `query_sales`，而是返回一个配置了工具声明的模型 Runnable：

```text
工具对象
-> 转成供应商工具 Schema
-> 绑定到模型请求
-> 模型可以返回 tool_calls
```

所以：

```python
first = bound_model.invoke(messages)
```

得到的是 `AIMessage`。如果模型决定调用工具，调用请求在：

```python
first.tool_calls
```

应用程序必须自己完成：

```python
call = first.tool_calls[0]
tool = TOOLS[call["name"]]
result = tool.invoke(call["args"])
messages.append(ToolMessage(..., tool_call_id=call["id"]))
```

`bind_tools()` 解决“模型知道有哪些工具”，不解决“工具怎么执行、用户有没有权限”。

## 深入：一次工具调用的消息协议

完整消息序列是：

```text
HumanMessage
-> AIMessage(tool_calls=[...])
-> ToolMessage(tool_call_id=对应 call.id)
-> AIMessage(最终回答或新的 tool_calls)
```

`tool_call_id` 是关联键。工具结果不带正确的 ID，模型就无法可靠判断这个结果对应哪次请求，多个并行工具调用时尤其如此。

工具结果最好是结构化 JSON：

```json
{
  "success": false,
  "error_code": "FORBIDDEN",
  "message": "当前用户无权查询华东区",
  "retryable": false
}
```

不要把数据库堆栈、密钥或内部路径直接放进 `ToolMessage`。

## 深入：单轮 Tool Calling 为什么不是 Agent

本课手动流程通常是：

```text
模型 -> 执行工具 -> 模型 -> 结束
```

如果第二次模型仍返回 `tool_calls`，单轮实现通常不会继续处理。完整 Agent 需要循环：

```text
while not finished:
    message = model.invoke(messages)
    if not message.tool_calls:
        return message
    execute_tools(message.tool_calls)
    append_tool_messages()
```

循环还必须增加最大步数、超时、重复调用检测和错误分类，否则“模型会调用工具”会变成“模型可以无限调用工具”。

## 深入实验

### 实验一：观察 Schema

修改参数类型或 docstring，运行：

```python
print(query_sales.args_schema.model_json_schema())
```

观察哪些变化会进入模型看到的工具定义。

### 实验二：伪造非法参数

```python
query_sales.invoke({"month": "下个月", "region": "华东"})
```

分别观察 Schema 错误和函数内部业务错误，理解两层校验的差别。

### 实验三：故意修改 `tool_call_id`

把返回消息的 ID 改成不存在的值，观察第二次模型调用的错误，理解消息关联协议。

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
