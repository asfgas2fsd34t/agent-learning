# 04 Message 与提示词模板

> 来源：`尚硅谷-04-Message与提示词模板.pdf`。

## 学习目标

- 理解消息在 ChatModel 中的作用
- 掌握 System、Human、AI 和 Tool 四类核心消息
- 区分字符串、消息字典和消息对象
- 理解 `content` 与标准化 `content_blocks`
- 使用 `ChatPromptTemplate`、`MessagesPlaceholder` 和 `partial()`
- 正确组织多轮对话历史

## 1. 为什么需要 Message

补全模型主要接收字符串，对话模型需要区分消息来源：

```text
System：系统规则和角色
Human：用户输入
AI：模型回复或工具调用请求
Tool：工具执行结果
```

消息角色让模型能够理解：哪些内容是系统规则，哪些是用户问题，哪些是之前的模型回答，哪些是外部工具结果。

## 2. 核心消息类型

```python
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
```

### 2.1 `SystemMessage`

用于稳定的角色、目标和行为约束：

```python
SystemMessage(
    content="你是 Python 教师，只回答 Python 相关问题。"
)
```

系统提示词可以引导模型，但不能替代权限、参数校验和业务规则。

### 2.2 `HumanMessage`

表示用户输入：

```python
HumanMessage(content="什么是生成器？")
```

### 2.3 `AIMessage`

表示模型输出：

```python
AIMessage(content="生成器是一种惰性迭代工具。")
```

它还可能携带：

- `tool_calls`
- `invalid_tool_calls`
- `usage_metadata`
- `response_metadata`
- 消息 ID

### 2.4 `ToolMessage`

表示工具执行后的结果：

```python
ToolMessage(
    content='{"temperature": 18}',
    tool_call_id="call_001",
    name="get_weather",
)
```

`tool_call_id` 必须对应之前 `AIMessage.tool_calls` 中的 ID，这样模型才能知道结果属于哪次工具调用。

## 3. 消息的三种输入格式

### 3.1 字符串

```python
model.invoke("你好")
```

适合单轮简单调用。

### 3.2 消息字典

```python
messages = [
    {"role": "system", "content": "你是 Python 教师"},
    {"role": "user", "content": "解释一下闭包"},
]
```

常见角色是 `system`、`user`、`assistant` 和 `tool`。

### 3.3 消息对象

```python
messages = [
    SystemMessage(content="你是 Python 教师"),
    HumanMessage(content="解释一下闭包"),
]
```

消息对象类型明确，适合读取 Tool Call、Token 和其他结构化属性。

## 4. 消息常见字段

### 4.1 基础字段

| 字段 | 作用 |
|---|---|
| `content` | 文本或多模态内容 |
| `id` | 消息标识 |
| `name` | 可选名称 |
| `additional_kwargs` | 提供商扩展数据 |
| `response_metadata` | 响应元数据 |

`AIMessage` 额外关注：

```text
tool_calls
invalid_tool_calls
usage_metadata
```

`ToolMessage` 额外关注：

```text
tool_call_id
status
artifact
```

字段是否存在和具体结构取决于消息类型和模型提供商。

## 5. `content` 与 `content_blocks`

### 5.1 `content`

纯文本消息：

```python
message = HumanMessage(content="描述这张图片")
```

多模态消息可以使用字典列表，但字典格式通常和提供商协议有关。

### 5.2 `content_blocks`

`content_blocks` 提供跨提供商更统一的内容块视图，可以表示：

- 文本
- 图片
- 音频
- 推理内容
- Tool Call
- 引用和其他标准块

```python
for block in response.content_blocks:
    print(block)
```

可以这样理解：

```text
content：底层或兼容性的原始内容
content_blocks：LangChain 标准化后的内容块
```

不要假设所有模型都支持所有多模态块。

## 6. 多轮对话历史

```python
messages = [
    SystemMessage(content="你是 Python 教师"),
    HumanMessage(content="我叫小王"),
]

response = model.invoke(messages)
messages.append(response)

messages.append(HumanMessage(content="我叫什么？"))
response = model.invoke(messages)
```

关键点：

```text
模型不会自动记住上一次请求
应用必须传入历史，或使用 Checkpointer 管理会话状态
```

手工列表适合解释原理；长期运行的 Agent 应使用状态和记忆治理，避免历史无限增长。

## 7. 为什么需要提示词模板

直接拼接字符串：

```python
prompt = "请把" + text + "总结为" + str(length) + "字"
```

容易产生：

- 变量边界不清
- 角色消息混乱
- 模板难复用
- 多轮历史难插入
- 修改和测试困难

`ChatPromptTemplate` 把消息结构和动态变量分开管理。

## 8. 创建 `ChatPromptTemplate`

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一名{role}"),
        ("human", "请回答：{question}"),
    ]
)
```

调用模板：

```python
prompt_value = prompt.invoke(
    {
        "role": "Python 教师",
        "question": "什么是迭代器？",
    }
)
```

返回 `ChatPromptValue`，其中包含消息列表：

```python
print(prompt_value.messages)
```

## 9. 模板的输入方式

### 9.1 字典

多个变量时使用字典：

```python
prompt.invoke(
    {
        "role": "教师",
        "question": "什么是闭包？",
    }
)
```

### 9.2 单变量简写

模板只有一个变量时，可以直接传值，但为了可读性和后续扩展，工程代码通常仍推荐字典。

### 9.3 与模型组合

```python
chain = prompt | model

response = chain.invoke(
    {
        "role": "Python 教师",
        "question": "什么是闭包？",
    }
)
```

Prompt 是 Runnable，因此可以用 LCEL 和 Model 组合。

## 10. 模板支持的消息元素

`from_messages()` 可以接收：

- `(role, template)` 元组
- 已创建的 `BaseMessage`
- `SystemMessagePromptTemplate`
- `HumanMessagePromptTemplate`
- `MessagesPlaceholder`
- 嵌套的 Prompt Template

固定消息适合不变内容，模板消息适合动态变量。

## 11. `MessagesPlaceholder`

它用于把一组消息插入模板指定位置：

```python
from langchain_core.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个有帮助的助手"),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)
```

调用：

```python
prompt_value = prompt.invoke(
    {
        "history": [
            HumanMessage(content="我在学习 Python"),
            AIMessage(content="我们可以从基础语法开始"),
        ],
        "question": "我刚才说在学什么？",
    }
)
```

也可以使用简写：

```python
("placeholder", "{history}")
```

占位符只负责插入消息，不负责保存或裁剪历史。

## 12. `partial()` 预填充变量

```python
base_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是{role}，使用{language}回答"),
        ("human", "{question}"),
    ]
)

python_prompt = base_prompt.partial(
    role="Python 教师",
    language="中文",
)
```

后续只传剩余变量：

```python
python_prompt.invoke({"question": "什么是生成器？"})
```

适合：

- 创建不同角色的模板变体
- 预填充固定格式
- 注入调用时才计算的动态值

不要把 API Key、权限信息等安全数据作为普通 Prompt 变量使用。

## 13. 模板复用和组合

可以拆分为：

```text
公共系统规则
领域规则
历史消息
当前用户问题
输出要求
```

模板复用的目标是减少重复并保持行为一致，但不要把所有场景都塞进一个巨大模板。角色和业务边界不同的场景应使用独立模板并进行版本管理。

## 14. 常见错误

### 14.1 只传最后一个用户问题

多轮问题中的代词和上下文会丢失。

### 14.2 把 Tool 结果写成 HumanMessage

模型无法准确关联工具调用，应使用对应 `tool_call_id` 的 `ToolMessage`。

### 14.3 把模板当成权限控制

System Prompt 不能阻止越权访问，权限必须由应用和工具执行层校验。

### 14.4 历史无限增长

消息最终会超过上下文窗口，需要在记忆章节使用裁剪、删除、摘要和 Checkpointer。

## 总结

```text
Message：描述谁说了什么，以及工具返回了什么
ChatPromptTemplate：生成结构化消息列表
MessagesPlaceholder：插入历史消息
partial：预填充固定变量
content_blocks：标准化多模态内容
```

消息协议是 Tool Calling、Agent、Middleware 和 Memory 的共同基础。
