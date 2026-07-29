# 05 Tools

> 来源：`尚硅谷-05-Tools.pdf`。

## 学习目标

- 理解 Tool 和普通 Python 函数的关系
- 掌握 `@tool`、名称、描述和参数 Schema
- 使用 `bind_tools()` 把工具声明交给模型
- 完成 Tool Call、应用执行和 `ToolMessage` 回传
- 理解多工具调用和 `tool_choice`
- 掌握工具设计的基本原则

## 1. 什么是 Tool

大模型只能生成内容，Tool 让应用能够访问外部能力：

- 搜索和知识检索
- 天气、地图等 API
- 数据库查询
- 文件读写
- 计算和代码执行
- 订单、邮件等业务操作

在 LangChain 中，Tool 是带有明确名称、描述、输入 Schema 和执行逻辑的可调用对象。

```text
普通函数：应用代码决定何时调用
Tool：模型可以根据描述提出调用请求
```

模型提出请求不等于模型亲自执行。真正执行仍由应用程序完成。

## 2. 两种调用方式

### 2.1 直接调用

适合测试工具本身：

```python
result = get_weather.invoke({"city": "北京"})
```

### 2.2 绑定模型

```python
model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke("北京今天天气如何？")
```

模型根据问题和 Tool Schema 决定是否生成 `tool_calls`。

## 3. Tool Calling 完整流程

```text
1. 应用定义 Tool
2. bind_tools 把 Tool Schema 交给模型
3. 用户提出问题
4. 模型返回 AIMessage.tool_calls
5. 应用校验并执行 Tool
6. 应用构造 ToolMessage
7. ToolMessage 交回模型
8. 模型生成最终回答
```

模型返回的 Tool Call 通常包含：

```python
{
    "name": "get_weather",
    "args": {"city": "北京"},
    "id": "call_001",
    "type": "tool_call",
}
```

## 4. 不使用 `@tool` 定义

带类型标注和 Docstring 的普通函数可以被转换为工具：

```python
def get_weather(city: str) -> str:
    """查询指定城市的天气。"""
    return f"{city}天气晴朗"


model_with_tools = model.bind_tools([get_weather])
```

LangChain 会读取：

```text
函数名 -> Tool 名称
Docstring -> Tool 描述
参数名和类型 -> JSON Schema
```

## 5. 使用 `@tool`

```python
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。"""
    return f"{city}天气晴朗"
```

装饰后，`get_weather` 已经是 Tool 对象：

```python
print(get_weather.name)
print(get_weather.description)
print(get_weather.args)
print(get_weather.args_schema)
```

直接测试：

```python
print(get_weather.invoke({"city": "北京"}))
```

## 6. Tool 描述为什么重要

模型通过名称、描述和参数说明选择工具：

```python
@tool(description="查询指定城市当前天气，不提供历史天气")
def get_weather(city: str) -> str:
    ...
```

描述应包含：

- 工具解决什么问题
- 什么时候应该使用
- 重要输入含义
- 明确边界和不支持范围

避免：

- 名称模糊，例如 `handle_data`
- 描述过长，包含大量业务实现
- 多个工具描述高度重叠
- 暗示模型拥有实际不存在的权限

## 7. 参数 Schema

### 7.1 类型标注和默认值

```python
@tool
def search_news(
    keyword: str,
    limit: int = 5,
) -> list[str]:
    """按关键词查询最近新闻。"""
    ...
```

类型、默认值和 Docstring 会形成参数 Schema。

### 7.2 Pydantic `args_schema`

参数复杂时使用 Pydantic：

```python
from typing import Literal

from pydantic import BaseModel, Field


class WeatherInput(BaseModel):
    city: str = Field(description="城市名称，例如北京")
    unit: Literal["celsius", "fahrenheit"] = "celsius"


@tool(args_schema=WeatherInput)
def get_weather(city: str, unit: str = "celsius") -> str:
    """查询当前天气。"""
    ...
```

Pydantic 可以表达枚举、范围、格式和字段说明，也会在执行前做运行时校验。

### 7.3 JSON Schema

需要直接对接已有协议时，也可以提供 JSON Schema。它更底层、更灵活，但维护成本通常高于 Pydantic。

### 7.4 查看 OpenAI Tool Schema

```python
from langchain_core.utils.function_calling import convert_to_openai_tool

print(convert_to_openai_tool(get_weather))
```

这有助于理解最终发送给模型的名称、描述和参数结构。

## 8. 执行 Tool Call

```python
from langchain_core.messages import HumanMessage, ToolMessage

messages = [HumanMessage(content="北京今天天气如何？")]
response = model_with_tools.invoke(messages)
messages.append(response)

for tool_call in response.tool_calls:
    if tool_call["name"] == get_weather.name:
        result = get_weather.invoke(tool_call["args"])
        messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )
        )

final_response = model_with_tools.invoke(messages)
```

必须先把包含 Tool Call 的 `AIMessage` 放入历史，再添加对应的 `ToolMessage`。

部分 LangChain Tool 支持把完整 `ToolCall` 传给 `.invoke()`，并自动生成关联的 `ToolMessage`；使用时应确认当前 Tool 和版本的返回类型。

## 9. 多工具调用

```python
model_with_tools = model.bind_tools(
    [get_weather, search_news]
)
```

模型一次可能返回多个 Tool Call：

```text
查询北京天气
查询今日新闻
```

应用需要：

1. 遍历全部 Tool Call
2. 根据名称查找允许的 Tool
3. 校验每组参数
4. 执行并生成对应 `ToolMessage`
5. 再次调用模型

多个只读工具可以并行；具有写副作用的工具应经过权限、幂等和审批控制。

## 10. `tool_choice`

绑定工具时可以控制模型是否必须调用工具：

```python
model_with_tools = model.bind_tools(
    [get_weather],
    tool_choice="auto",
)
```

常见值：

| 值 | 含义 |
|---|---|
| `none` | 禁止调用工具 |
| `auto` | 模型自行决定 |
| `required` / `any` | 必须调用至少一个工具，是否支持取决于提供商 |
| 指定工具 | 强制调用特定工具 |

不要为了“提高工具使用率”而默认强制调用工具。简单问题不需要工具时，强制调用会增加成本和错误。

## 11. Tool 返回值

工具结果应该：

- 结构清晰
- 字段稳定
- 明确成功或失败
- 不返回无关大文本
- 不泄露敏感内部数据

示例：

```python
{
    "ok": True,
    "data": {
        "city": "北京",
        "temperature": 18,
    },
    "error_code": None,
}
```

Tool 返回值是交给模型的 Observation，不应把底层异常堆栈直接暴露给模型或用户。

## 12. 设计经验

### 12.1 单一职责

一个工具只解决一个明确问题。查询订单和执行退款应是两个工具。

### 12.2 名称稳定

工具名是模型选择和日志分析的重要协议，发布后不要随意修改。

### 12.3 参数最小化

只让模型提供业务意图需要的参数。用户身份、租户、权限和幂等键应由可信运行时注入。

### 12.4 执行前校验

```text
Schema 校验
-> 身份和权限
-> 资源归属
-> 业务状态
-> 风险和审批
-> 幂等
-> 执行
```

### 12.5 失败可理解

返回稳定错误码，让 Agent 能区分参数错误、权限错误、临时失败和结果未知。

## 13. Tool 与 Agent

手动 Tool Calling 需要应用自己维护循环。`create_agent()` 会封装：

```text
模型调用
-> 是否有 Tool Call
-> 执行 Tool
-> 追加 ToolMessage
-> 再次调用模型
-> 直到得到最终答案
```

理解本章的手动流程，是理解 Agent 内部机制的前提。

## 总结

```text
@tool：把函数变成结构化工具
bind_tools：把 Tool Schema 交给模型
AIMessage.tool_calls：模型提出的调用请求
ToolMessage：应用执行后的观察结果
tool_choice：控制是否必须调用工具
args_schema：约束工具参数
```

Tool 让模型能够提出行动，但真实执行权始终属于应用程序。
