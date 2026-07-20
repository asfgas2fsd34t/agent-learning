# 01 LangChain 基础：从原生调用到可组合链

> 前置知识：[00 Pydantic 基础](00-Pydantic基础.md)。如果还不熟悉 `BaseModel`、`Field` 和 `model_dump_json()`，建议先阅读这份笔记。

## 1. 这节课解决什么问题

前面的原生 Python 练习已经手动实现过：

- 构造 `messages`
- 调用大模型 API
- 解析模型返回值
- 循环执行工具
- 保存会话记忆

这些原理仍然有效。LangChain 不是替代这些原理，而是把常见步骤封装成统一对象，让它们可以组合、替换、测试和观测。

本课只学习五个基础能力：

1. `ChatModel`：统一的聊天模型接口
2. `Messages`：有明确角色的消息对象
3. `ChatPromptTemplate`：可复用的提示词模板
4. `Runnable`：统一执行接口和链式组合
5. `Structured Output`：让结果直接成为经过校验的 Python 对象

工具绑定和 Agent 循环会放到下一课。

## 2. 整体流程

```mermaid
flowchart LR
    A["输入数据 dict"] --> B["ChatPromptTemplate"]
    B --> C["PromptValue / Messages"]
    C --> D["ChatModel"]
    D --> E["AIMessage"]
    E --> F["输出解析器或结构化对象"]
```

最典型的 LangChain 表达式是：

```python
chain = prompt | model | parser
result = chain.invoke({"text": "需要处理的文本"})
```

这里的 `|` 不是字符串拼接。它把多个实现了 `Runnable` 协议的组件连接成 `RunnableSequence`：前一个组件的输出会成为后一个组件的输入。

## 3. ChatModel：统一模型调用接口

### 3.1 它是什么

`ChatModel` 可以理解为“聊天模型适配器”。它不是通常直接实例化的某个类：通用抽象是 `BaseChatModel`，`ChatOpenAI` 是其中一个具体实现。业务代码面对统一的 `invoke`、`stream`、`batch` 等接口，具体模型供应商的差异由对应集成包处理。

OpenAI 及 OpenAI-compatible 服务通常使用：

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="your-model-name",
    api_key="your-api-key",
    base_url="https://example.com/v1",
    temperature=0,
)
```

调用方式：

```python
response = model.invoke("什么是 Agent？")
print(response.content)
```

`response` 通常是 `AIMessage`，不只是一个字符串。除正文外，它还可能携带工具调用、token 用量、响应 ID 等元数据。

### 3.2 与原生 SDK 的关系

原生 SDK 常见写法：

```python
response = client.chat.completions.create(
    model=model_name,
    messages=messages,
)
answer = response.choices[0].message.content
```

LangChain 写法：

```python
response = model.invoke(messages)
answer = response.content
```

LangChain 减少的是不同模型之间的接入差异，不会替你解决权限、幂等、业务校验、超时重试和数据真实性问题。

## 4. Messages：带角色的消息

### 4.1 常见消息类型

| 类型 | 对应角色 | 主要用途 |
| --- | --- | --- |
| `SystemMessage` | system | 定义长期规则、身份和行为边界 |
| `HumanMessage` | user | 用户本轮输入 |
| `AIMessage` | assistant | 模型回答，也可能包含工具调用 |
| `ToolMessage` | tool | 工具执行后返回给模型的结果 |

示例：

```python
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage  # 仅在需要基类类型标注时导入

messages: list[BaseMessage] = [
    SystemMessage(content="你是 Agent 开发导师，回答要准确简洁。"),
    HumanMessage(content="什么是 Runnable？"),
]

response = model.invoke(messages)
```

当前 `langchain.messages` 会重新导出常用的具体消息类，但不导出 `BaseMessage`。需要给消息列表添加通用类型标注时，应从 `langchain_core.messages` 导入 `BaseMessage`。

### 4.2 为什么不一直使用字典

原生字典仍然能表达消息，但消息类有三个优势：

- 类型更明确，编辑器和类型检查工具更容易发现错误
- 能表达工具调用、工具结果等更复杂的数据
- 能直接参与 LangChain 的模板、历史记录和 Runnable 组合

消息类型只是结构化表达，不会自动防止提示词注入。系统权限仍必须由业务代码控制。

## 5. ChatPromptTemplate：可复用模板

### 5.1 基本用法

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一名{role}，只根据输入内容回答。"),
        ("human", "请总结以下内容：\n{text}"),
    ]
)

prompt_value = prompt.invoke(
    {
        "role": "Agent 开发导师",
        "text": "LangChain 为模型调用提供统一的可组合接口。",
    }
)
```

模板负责把输入变量变成消息，模型负责推理。把两者分开后，同一个模型可以复用多套模板，同一套模板也可以切换模型。

### 5.2 模板不是普通字符串替换工具

模板的输出是 `PromptValue`，它可以继续转换为消息列表：

```python
messages = prompt_value.to_messages()
```

生产环境要注意：

- 明确区分系统指令、外部知识和用户输入
- 不要把用户输入直接拼进系统规则
- 外部数据即使放进模板，也仍然是不可信输入
- 模板只负责组织上下文，不负责业务权限

## 6. Runnable：LangChain 的统一执行协议

### 6.1 四个常见执行方法

| 方法 | 用途 |
| --- | --- |
| `invoke(input)` | 同步处理单个输入 |
| `ainvoke(input)` | 异步处理单个输入 |
| `batch(inputs)` | 批量处理多个输入 |
| `stream(input)` | 流式返回结果 |

并不是每个场景都应该立刻使用异步或批处理。学习阶段先掌握 `invoke`，在线服务再根据吞吐和延迟要求选择执行方式。

### 6.2 使用 `|` 组合

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | model | StrOutputParser()
answer = chain.invoke({"text": "LangChain 基础内容"})
```

数据依次发生三次转换：

```text
{"text": "..."}
    -> PromptValue
    -> AIMessage
    -> str
```

`StrOutputParser` 把 `AIMessage` 的正文转换成字符串，所以调用方不再需要手动读取 `response.content`。

### 6.3 组合的真正价值

链式写法的价值不只是少写几行代码，而是形成清晰边界：

- 模板只负责构造输入
- 模型只负责推理
- 解析器只负责转换输出
- 每一部分都能单独替换和测试

一条链不应该无限变长。复杂流程涉及分支、循环、状态和人工确认时，应进入 LangGraph 等工作流方案，而不是继续堆叠线性 `|`。

## 7. Structured Output：结构化输出

### 7.1 为什么仅要求“返回 JSON”不够

下面的提示词约束比较弱：

```text
请只返回 JSON，字段为 topic、key_points、summary。
```

模型仍可能返回 Markdown 代码块、漏字段、字段类型错误或额外说明。业务代码还需要解析和校验。

LangChain 可以结合 Pydantic 定义结果结构：

```python
from pydantic import BaseModel, Field


class StudyNote(BaseModel):
    topic: str = Field(description="主题")
    key_points: list[str] = Field(description="关键知识点")
    summary: str = Field(description="一句话总结")
```

然后让模型按这个结构输出：

```python
structured_model = model.with_structured_output(
    StudyNote,
    method="function_calling",
)

note = structured_model.invoke("整理 Runnable 的学习要点")
print(note.topic)
print(note.key_points)
```

当传入 Pydantic 模型时，成功结果会直接成为 `StudyNote` 对象，并经过字段类型校验。

### 7.2 `function_calling` 的含义

这里借用了模型的工具调用能力来约束参数结构，但不会执行真实业务工具。模型只是按照 `StudyNote` 的 schema 生成参数，LangChain 再把参数解析成对象。

不同供应商对结构化输出方式的支持并不完全相同。使用 OpenAI-compatible 服务时，需要确认它是否正确实现 tool calling；不能只看接口地址兼容。

OpenAI-compatible 通常只说明请求路径和主要字段相似，并不保证原生 `json_schema`、Responses API、流式 token 用量等扩展能力完全兼容。本练习显式使用兼容面更广的 `function_calling`，上线前仍要用目标模型做集成测试。

`ChatOpenAI.with_structured_output()` 常见的三种模式是：

| 模式 | 约束方式 | 注意事项 |
| --- | --- | --- |
| `function_calling` | 使用工具调用参数 schema | 兼容服务也必须支持 Tool Calling |
| `json_schema` | 使用 OpenAI 原生 Structured Outputs | 只适用于明确支持该能力的模型和接口 |
| `json_mode` | 要求模型返回合法 JSON | 提示词仍需说明字段，约束相对更弱 |

生产环境排查解析问题时，可以研究 `include_raw=True`。它会同时保留模型原始消息、解析结果和解析错误；但日志中可能包含用户数据，必须先做脱敏和访问控制。

### 7.3 结构化输出仍需业务校验

类型正确不代表业务正确。例如退款金额是数字，不代表它没有超过订单可退金额。因此仍需要：

- Pydantic：格式和基本类型校验
- 业务服务：权限、状态、金额、幂等校验
- 数据来源：真实性与时效性校验

## 8. 深入：一次 `invoke()` 到底发生了什么

把 `model.invoke("什么是 Agent？")` 当成“调用一个函数”是不够的。要理解 LangChain，至少要知道它在统一接口下面做了哪些转换。

### 8.1 输入归一化

`ChatModel` 接受的输入不只有字符串，还可能是消息列表或 `PromptValue`：

```text
str
list[BaseMessage]
PromptValue
```

模型适配器会先把它们归一化为 `PromptValue`，再转换成供应商 API 所需的消息结构：

```text
用户输入
-> ChatModel._convert_input
-> PromptValue
-> 供应商消息格式
-> HTTP 请求
```

因此下面三种调用在语义上接近，但类型边界不同：

```python
model.invoke("什么是 Agent？")
model.invoke([HumanMessage(content="什么是 Agent？")])
model.invoke(prompt.invoke({"topic": "Agent"}))
```

生产代码中不要依赖“什么都能传”的宽松行为。建议在模块边界明确输入类型，让模板负责把业务字典转换为消息。

### 8.2 模型适配器的内部边界

可以把调用链抽象成：

```text
BaseChatModel.invoke
-> generate_prompt
-> _generate_with_cache
-> 供应商 ChatOpenAI._generate
-> HTTP 客户端
-> ChatResult
-> AIMessage
```

不同供应商真正不同的部分主要在 `_generate`：

- 如何组织 HTTP 请求
- 如何传递模型名和模型参数
- 如何把响应转换成 `AIMessage`
- 如何提取 usage、finish_reason、tool_calls 等元数据

上层业务使用 `invoke()`，因此可以替换供应商；但这不等于所有供应商能力完全一致。工具调用、结构化输出、流式用量和多模态字段仍需要集成测试。

### 8.3 `AIMessage` 为什么必须保留

如果模型调用只返回字符串，调用方会丢掉大量控制信息。`AIMessage` 可能包含：

```text
content              正文
tool_calls           工具调用请求
response_metadata    服务商响应元数据
usage_metadata       token 使用量
id                   响应标识
```

链的最后一步才适合把它转换成字符串：

```python
chain = prompt | model | StrOutputParser()
```

如果过早调用 `response.content`，后续就无法自然地读取工具调用和 token 信息。这是“解析器应该尽量靠近输出边界”的原因。

## 9. 深入：`Runnable` 的真正契约

### 9.1 `Runnable` 不是只提供 `invoke`

一个 Runnable 的核心契约可以表示为：

```text
Runnable[Input, Output]
```

它约定了执行形态，但不保证每个组件对所有执行方式都拥有同样的性能：

| 方法 | 语义 | 工程注意事项 |
|---|---|---|
| `invoke` | 一个输入得到一个输出 | 最容易调试，适合同步单请求 |
| `ainvoke` | 异步处理一个输入 | 下游和中间函数也要正确支持异步 |
| `batch` | 多个输入得到多个输出 | 可能是客户端并发，不一定是供应商批量 API |
| `stream` | 逐步产出结果 | 只有支持流式的下游才有真实增量效果 |

不要因为看到 `batch()` 就认为调用了一次“批量模型接口”。很多 Runnable 的默认实现只是并发执行多个 `invoke()`。是否真正降低成本，要看供应商 API、并发限制和服务端计费。

### 9.2 `|` 只负责组装，不负责执行

```python
chain = prompt | model | parser
```

这一步创建的是 `RunnableSequence`，不会发起网络请求。真正执行时，输入会按顺序流动：

```text
dict[str, str]
-> ChatPromptTemplate
-> PromptValue
-> ChatOpenAI
-> AIMessage
-> StrOutputParser
-> str
```

所以每一段都必须满足类型契约：

```text
上一个组件的输出类型 = 下一个组件能接受的输入类型
```

常见错误不是模型错误，而是链的边界错误：

```python
prompt = ChatPromptTemplate.from_template("{text}")
chain = prompt | (lambda value: value.upper())
```

这里 Lambda 接收到的不是原始字典，而是 PromptValue。若函数误以为输入仍然是 `dict`，就会在运行时失败。

### 9.3 `RunnableLambda` 的边界

```python
def normalize_text(value: dict[str, str]) -> str:
    return value["text"].strip()


chain = RunnableLambda(normalize_text) | prompt | model
```

`RunnableLambda` 适合确定性逻辑，但不应把复杂业务流程全部塞进去：

- 纯字段转换可以放入
- 权限、事务、幂等应放在业务服务
- 多分支和循环应使用显式 Workflow
- 隐藏网络请求会让链难以测试和观测

一个函数能否放入 Runnable，不只看它能不能运行，还要看它的副作用是否清晰。

## 10. `RunnableConfig`：配置如何沿链传播

Runnable 的配置与业务输入是两条不同的数据流：

```python
chain.invoke(
    {"text": "Runnable"},
    config={
        "tags": ["learning", "summary"],
        "metadata": {"user_id": "user_1001"},
    },
)
```

常用配置：

- `tags`：给 Trace 和回调分类
- `metadata`：附加观测信息
- `callbacks`：接收开始、结束、错误等事件
- `max_concurrency`：批量执行时的并发上限
- `configurable`：传递给可配置 Runnable 的运行时参数

关键区别：

```text
业务输入：会改变模型要处理的内容
RunnableConfig：控制执行和观测方式
```

不要把用户问题塞进 `metadata`，也不要把权限判断只放在 `tags` 中。配置可以被组件读取，但不是安全边界。

### 10.1 配置与状态不是一回事

```text
RunnableConfig：本次调用的执行配置
Agent State：Agent 循环中需要持续变化的任务状态
Memory：跨调用或跨会话保存的信息
```

例如：

```text
trace_id       适合 metadata
当前用户       适合受控 runtime/context
已完成步骤     适合 Agent State
用户默认单位   适合长期 Memory
```

混用这些概念会导致权限泄露、状态丢失或链难以复现。

## 11. Structured Output 的完整失败链路

`with_structured_output(StudyNote)` 不是“模型天然返回 Python 对象”，而是多个步骤的组合：

```text
Pydantic Schema
-> 转成模型可理解的结构约束
-> 模型生成结构化参数或 JSON
-> LangChain 解析响应
-> Pydantic 校验类型
-> 返回 StudyNote
```

失败可能发生在不同层：

| 层 | 失败示例 | 处理方式 |
|---|---|---|
| 模型选择 | 模型不支持指定结构化方式 | 换 method 或模型，做启动检查 |
| 语法解析 | 返回了非法 JSON | 记录原始响应，有限重试 |
| 类型校验 | `key_points` 返回字符串 | 修正提示或重试 |
| 业务校验 | 金额超过订单可退上限 | 业务服务拒绝，不能只靠 Pydantic |
| 数据真实性 | 内容与数据库不符 | 回查真实数据源 |

因此结构化输出解决的是“结构可解析”，不是“事实正确”或“业务安全”。

## 12. 可运行的深度实验

### 实验一：观察每一段的输入输出

在 `practice/05-langchain-basics/src/langchain_basics/chains.py` 中，把链拆成三个独立变量：

```python
prompt_value = SUMMARY_PROMPT.invoke({"text": "Runnable 是组合协议"})
print(type(prompt_value))

message = model.invoke(prompt_value)
print(type(message))
print(message.response_metadata)

answer = StrOutputParser().invoke(message)
print(type(answer))
```

预期观察：

```text
PromptValue -> AIMessage -> str
```

### 实验二：故意破坏 Runnable 类型契约

```python
chain = SUMMARY_PROMPT | RunnableLambda(lambda value: value["text"])
```

运行后观察：`RunnableLambda` 收到的是 PromptValue，而不是原始字典。这个错误能说明“链式表达式传递的是前一步输出”，而不是每一步都看到最初输入。

### 实验三：比较 `invoke` 和 `batch`

```python
inputs = [
    {"text": "第一段内容"},
    {"text": "第二段内容"},
]

answers = chain.batch(inputs, config={"max_concurrency": 2})
```

记录总耗时、请求数量和错误行为，不要只观察最终字符串。这个实验用于判断并发是否真的改善吞吐。

### 实验四：观察结构化输出失败

把 `StudyNote.key_points` 临时改成 `dict[str, str]`，再运行结构化模式，观察模型返回、解析器错误和 Pydantic 校验错误分别发生在哪里。

## 13. 本课应该形成的判断力

学完本课，不应只记住：

```text
LangChain 有 ChatModel、Prompt、Runnable 和 Parser。
```

而应能判断：

1. 当前问题是模型适配问题，还是 Runnable 输入输出契约问题？
2. 这个逻辑应该放在 Prompt、RunnableLambda、业务服务还是 Workflow？
3. 这个 `batch()` 是供应商批量接口，还是客户端并发？
4. 结构化输出失败发生在模型、解析器、Pydantic 还是业务校验层？
5. 这个信息应该进入业务输入、RunnableConfig、Agent State 还是 Memory？
6. 替换模型供应商后，哪些能力仍然兼容，哪些需要重新集成测试？

## 14. 本课完整案例

本项目的 `practice/05-langchain-basics` 实现了三个运行模式：

```text
chat       消息对象 -> ChatModel -> AIMessage
summary    Prompt Template -> ChatModel -> StrOutputParser
structured Prompt Template -> structured model -> StudyNote
```

运行前配置：

```powershell
Copy-Item .env.example .env
```

安装整个 workspace：

```powershell
python -m uv sync --all-packages
```

进入练习目录后运行：

```powershell
python -m uv run langchain-basics --mode chat
python -m uv run langchain-basics --mode summary
python -m uv run langchain-basics --mode structured
```

## 15. 生产环境边界

学习完本课后，需要明确下面这些责任不属于 LangChain 基础封装：

| 问题 | 应负责的层 |
| --- | --- |
| 用户能否退款 | 权限系统和业务服务 |
| 重复退款如何拦截 | 幂等与数据库约束 |
| 模型超时是否重试 | 应用层重试策略 |
| 输出字段是否合法 | Pydantic + 业务校验 |
| 外部知识是否最新 | RAG 数据治理 |
| 复杂 Agent 如何循环 | Agent/LangGraph 工作流 |

LangChain 是编排和集成工具，不是业务安全边界。

## 16. 学完后的自测问题

1. `ChatModel` 和真实大模型是什么关系？
2. `AIMessage` 为什么不直接设计成字符串？
3. `ChatPromptTemplate` 的输入和输出分别是什么？
4. `prompt | model | parser` 中数据如何变化？
5. `invoke`、`batch`、`stream` 分别适合什么场景？
6. 结构化输出为什么比“提示模型返回 JSON”更可靠？
7. Pydantic 校验通过后，为什么仍然需要业务校验？

## 17. 官方资料

- [LangChain Installation](https://docs.langchain.com/oss/python/langchain/install)
- [ChatOpenAI Integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [LangChain Models](https://docs.langchain.com/oss/python/langchain/models)
- [LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)
- [LangChain Structured Output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [BaseChatModel API Reference](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel)
- [ChatPromptTemplate API Reference](https://reference.langchain.com/python/langchain-core/prompts/ChatPromptTemplate)
- [Runnable API Reference](https://reference.langchain.com/python/langchain-core/runnables/Runnable)
- [ChatOpenAI API Reference](https://reference.langchain.com/python/integrations/langchain_openai/ChatOpenAI)

> 本课代码已使用 Python 3.11、`langchain==1.3.14`、`langchain-openai==1.3.5` 验证。不要照搬仍使用 `LLMChain.run()` 的旧版教程；当前新代码优先使用 Runnable、`|` 和 `invoke()`。
