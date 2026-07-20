# 02 Runnable 与 LCEL 深入

## 1. 本课目标

上一课看到了：

```python
chain = prompt | model | parser
```

这一课要进一步理解：

- `Runnable` 统一了什么
- `RunnableLambda` 如何包装普通函数
- `RunnablePassthrough` 如何保留并扩展输入
- `RunnableParallel` 如何并行计算多个字段
- `RunnableBranch` 如何根据条件选择分支
- `invoke`、`batch`、`stream` 和 `ainvoke` 的区别
- 如何测试一条由多个 Runnable 组成的 Chain

本课仍然不进入 Tool Calling 和 Agent 循环，先把 LangChain 的组合机制打牢。

## 2. Runnable 是什么

`Runnable` 是 LangChain 定义的可执行组件抽象，不是 Python 原生类。一个 Runnable 通常可以使用统一接口：

```python
runnable.invoke(input)
runnable.ainvoke(input)
runnable.batch(inputs)
runnable.stream(input)
```

LangChain 中常见的 Runnable 包括：

```text
ChatPromptTemplate
ChatOpenAI
StrOutputParser
PydanticOutputParser
RunnableLambda
RunnablePassthrough
RunnableParallel
RunnableBranch
RunnableSequence
```

它们职责不同，但都遵守同一套执行协议。

## 3. Runnable 的输入和输出

每个 Runnable 都可以看成一个函数：

```text
输入 -> Runnable -> 输出
```

例如：

```text
ChatPromptTemplate：dict -> PromptValue
ChatModel：PromptValue -> AIMessage
StrOutputParser：AIMessage -> str
```

组合以后：

```text
dict -> PromptValue -> AIMessage -> str
```

因此整个 Chain 可以声明为：

```python
Runnable[dict[str, str], str]
```

这表示它接收字符串字典，最后返回字符串。

## 4. `|` 和 RunnableSequence

```python
chain = prompt | model | parser
```

`|` 是 Python 原生运算符，但 LangChain 为 Runnable 重载了它的行为。它会创建一个 `RunnableSequence`：

```text
prompt -> model -> parser
```

`RunnableSequence` 自己也是 Runnable，所以还可以继续组合：

```python
chain = preprocess | prompt | model | parser
```

组合时不会调用模型：

```python
chain = prompt | model | parser
```

真正执行需要调用：

```python
answer = chain.invoke(input_data)
```

可以这样理解：

```text
创建 Chain：组装流水线
invoke：启动流水线
```

## 5. RunnableLambda

`RunnableLambda` 用于把普通 Python 函数包装成 Runnable：

```python
from langchain_core.runnables import RunnableLambda


def normalize_text(value: dict[str, str]) -> str:
    return " ".join(value["text"].strip().split())


normalizer = RunnableLambda(normalize_text)
```

调用：

```python
result = normalizer.invoke({"text": "  hello   world  "})
print(result)  # hello world
```

也可以继续组合：

```python
chain = normalizer | next_runnable
```

适合放进 `RunnableLambda` 的逻辑：

- 文本清洗
- 字段提取
- 日期格式转换
- 结果脱敏
- 构造下一步所需的输入
- 确定性的结果后处理

普通函数自身没有 `.invoke()`，但在 `|` 中 LangChain 通常可以自动把函数转换成 `RunnableLambda`。显式包装更容易理解、命名和测试。

## 6. RunnablePassthrough

`RunnablePassthrough()` 会把输入原样传递下去：

```python
from langchain_core.runnables import RunnablePassthrough


passthrough = RunnablePassthrough()
result = passthrough.invoke({"text": "hello"})
```

结果仍然是：

```python
{"text": "hello"}
```

### 6.1 `assign()` 增加字段

更常用的是：

```python
chain = RunnablePassthrough.assign(
    normalized_text=RunnableLambda(
        lambda value: value["text"].strip()
    ),
)
```

输入：

```python
{"text": "  hello  "}
```

输出：

```python
{
    "text": "  hello  ",
    "normalized_text": "hello",
}
```

`assign()` 保留原始字段，同时增加新字段，适合逐步丰富上下文。

## 7. RunnableParallel

```python
from langchain_core.runnables import RunnableLambda, RunnableParallel


analysis = RunnableParallel(
    normalized=RunnableLambda(
        lambda value: value["text"].strip()
    ),
    length=RunnableLambda(
        lambda value: len(value["text"])
    ),
)
```

调用：

```python
result = analysis.invoke({"text": "hello"})
```

结果：

```python
{
    "normalized": "hello",
    "length": 5,
}
```

两个分支接收同一个输入，再合并成一个字典：

```text
同一个输入
    -> normalized 分支
    -> length 分支
    -> 合并结果字典
```

当多个计算互不依赖时，可以使用 `RunnableParallel`。生产环境仍需设置并发度、超时、限流和费用上限。

## 8. RunnableBranch

```python
from langchain_core.runnables import RunnableBranch


branch = RunnableBranch(
    (
        lambda value: value["length"] > 80,
        long_chain,
    ),
    short_chain,
)
```

含义是：

```text
如果 length > 80，执行 long_chain
否则，执行 short_chain
```

最后一个分支是默认分支。建议始终提供默认分支，否则输入不满足条件时，流程可能无法得到明确结果。

分支前后的数据协议要对齐。例如两个分支都输出摘要字符串：

```text
long_chain  -> str
short_chain -> str
```

这样下游组件不需要判断当前走了哪条路径。

## 9. 完整自适应摘要链

本课练习的流程是：

```text
输入 text
-> Passthrough 保留原始字段
-> Parallel 并行计算清洗文本和长度
-> Branch 判断长文本还是短文本
-> 对应 Prompt
-> ChatModel
-> StrOutputParser
-> str
```

输入变化：

```python
{"text": "..."}
```

准备阶段后：

```python
{
    "text": "...",
    "normalized_text": "...",
    "text_length": 100,
}
```

然后分支根据 `text_length` 选择 Prompt。无论走哪条分支，最终都返回 `str`。

## 10. 四种执行方式

### 10.1 `invoke`

处理一个输入：

```python
answer = chain.invoke({"text": "学习内容"})
```

### 10.2 `batch`

批量处理多个输入：

```python
answers = chain.batch(
    [
        {"text": "第一段内容"},
        {"text": "第二段内容"},
    ]
)
```

结果是字符串列表。批量接口不等于无限并发，生产环境仍需控制并发和限流。

### 10.3 `stream`

流式返回结果：

```python
for chunk in chain.stream({"text": "学习内容"}):
    print(chunk, end="", flush=True)
```

它适合聊天界面逐步显示内容。但结构化输出不一定适合直接展示中间片段，最终结果仍应完整收集并校验。

### 10.4 `ainvoke`

异步执行：

```python
answer = await chain.ainvoke({"text": "学习内容"})
```

FastAPI 等异步服务可以使用它来管理并发等待。异步不等于单次请求一定更快。

## 11. 配置、重试和 fallback

### 11.1 配置运行名称

```python
named_chain = chain.with_config(
    {
        "run_name": "adaptive-summary",
        "tags": ["learning", "summary"],
    }
)
```

这类配置主要用于追踪和观测，不会改变业务结果。

### 11.2 有限重试

```python
retryable_chain = chain.with_retry(
    stop_after_attempt=2,
)
```

重试必须有边界。查询类操作可以谨慎重试；退款、下单等写操作不能因为 Chain 支持重试就重复执行业务动作。

### 11.3 fallback

```python
fallback_chain = primary_chain.with_fallbacks(
    [backup_chain]
)
```

备用 Chain 的输入输出协议必须兼容，不能只因为备用模型能返回字符串就直接交给后续业务。

## 12. 如何测试 Runnable

可以替换模型组件进行单元测试：

```python
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda


fake_model = RunnableLambda(
    lambda prompt: AIMessage(content="测试摘要")
)
```

这样可以测试模板、分支和解析器，而不调用真实 API。

但这只是单元测试。上线前仍需要真实端到端测试，验证目标模型、批量、流式和第三方接口兼容性。

## 13. Runnable、Tool 和 LangGraph 的边界

```text
Runnable：程序确定的一步处理
Tool：模型可以选择调用的能力
LangGraph：有状态、分支、循环和恢复的工作流
```

例如：

```text
每次请求都要清洗文本       -> Runnable
用户问订单时才查询订单     -> Tool
查询后分析、确认、恢复执行 -> LangGraph
```

不要因为 Runnable 可以组合，就把所有逻辑都塞成一条巨长 Chain。

## 14. 本课实践

实践目录：[practice/Agent开发实战/02-langchain-runnables](../../practice/Agent开发实战/02-langchain-runnables/README.md)

```powershell
cd practice/Agent开发实战/02-langchain-runnables
python -m uv run langchain-runnables --mode summary "Runnable 是 LangChain 的统一执行协议。"
python -m uv run langchain-runnables --mode batch
python -m uv run langchain-runnables --mode stream "请流式总结 Runnable 的作用。"
```

## 15. 自测问题

1. `Runnable` 和普通 Python 函数有什么区别？
2. `prompt | model | parser` 为什么返回的还是 Runnable？
3. `RunnableLambda` 适合放哪些逻辑？
4. `RunnablePassthrough.assign()` 为什么能保留原始字段？
5. `RunnableParallel` 的多个分支接收什么输入？
6. `RunnableBranch` 为什么需要默认分支？
7. `batch` 为什么不等于无限并发？
8. 为什么结构化输出不一定适合直接流式展示？
9. Runnable、Tool 和 LangGraph 的边界分别是什么？

## 16. Runnable 的底层执行模型

`prompt | model | parser` 最终不是把三个函数的源码拼在一起，而是创建一个嵌套的 Runnable 结构：

```text
RunnableSequence
  first: prompt
  middle: model
  last: parser
```

调用 `invoke(input, config)` 时，Sequence 依次执行每个组件，并把上一个组件的返回值交给下一个组件。任何一步抛出异常，默认都会终止后续步骤；后续组件不会收到“半成品结果”。

因此排查链路时要先问两个问题：

1. 当前组件实际收到的 Python 类型是什么？
2. 当前组件返回的类型是否是下一组件的输入契约？

```python
RunnableLambda(lambda value: value["question"]) | prompt
```

这里 Lambda 返回 `str`，而 Prompt 需要包含变量的 `dict`，链路会在运行时失败。IDE 的类型提示可以帮助发现问题，但不能替代一次真实 `invoke`。

## 17. Parallel 的并行不是状态共享

`RunnableParallel` 的每个分支都拿到同一份输入快照：

```text
input
  ├─ branch_a(input)
  └─ branch_b(input)
       -> {a: result_a, b: result_b}
```

分支 A 计算出的字段不会自动出现在分支 B 的输入里。需要“先计算再使用”时，应使用 Sequence 或 `RunnablePassthrough.assign()`：

```python
prepared = RunnablePassthrough.assign(
    normalized=RunnableLambda(lambda value: value["text"].strip())
)
chain = prepared | RunnableParallel(
    text=RunnableLambda(lambda value: value["normalized"]),
    length=RunnableLambda(lambda value: len(value["normalized"])),
)
```

并行分支还要注意副作用：两个分支同时写同一文件、更新同一数据库记录或重复调用收费接口，可能造成竞态和重复执行。Parallel 适合独立的只读计算，不是自动获得事务一致性的工具。

## 18. Config、Callbacks 和业务输入是三种不同信息

```python
config = {
    "run_name": "sales-summary",
    "tags": ["bi", "read-only"],
    "metadata": {"request_id": "req-1"},
    "max_concurrency": 4,
}
chain.invoke({"question": "本月销售额"}, config=config)
```

这类 `config` 用于运行控制和观测，不应承载 `user_id`、租户权限等需要进入业务校验的数据，除非你的服务明确把它们从可信请求上下文注入并保护好。模型生成的业务参数更不能覆盖这些值。

```text
业务输入：问题、订单号、查询月份
可信运行上下文：request_id、user_id、tenant_id、权限
Agent State：消息、工具结果、尝试次数、路由状态
Runnable Config：tags、callbacks、并发和追踪信息
```

混淆这些边界会产生典型漏洞：把 `tenant_id` 放进模型可修改的 prompt 字典，或者把不可信的用户输入写进 callbacks metadata 后再当作权限依据。

## 19. batch、async、stream 的真实取舍

| 接口 | 适合 | 常见误解 |
| --- | --- | --- |
| `invoke` | 单次同步任务 | 调用本身不等于线程安全 |
| `batch` | 多个独立输入 | 不保证供应商真的使用批量 API |
| `ainvoke` | 异步服务中的等待 | 不会让模型推理本身变快 |
| `stream` | 首字延迟和交互体验 | 不能把半截结构化 JSON 当最终结果 |

在真实供应商上验证：请求是否并发、限流如何返回、失败是否部分成功、流式中断如何取消。对写操作不要直接用 `batch` 或重试包装，除非业务接口有幂等键。

## 20. 错误传播与重试边界

Runnable 默认把异常向上传播。`with_retry()` 只知道如何重新运行 Runnable，并不知道这个 Runnable 是否已经产生副作用：

```text
模型超时、429、临时网络错误 -> 可能重试
参数校验错误、权限错误       -> 不应重试
下单/退款执行后响应丢失       -> 查询状态，不要盲重试
```

更稳妥的方式是让底层服务返回结构化错误码，再由服务层决定是否重试，而不是在整个 Agent Chain 外面无差别套 `with_retry()`。

## 21. 可执行实验：打破和修复类型契约

```python
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough


bad = RunnableLambda(lambda value: value["text"]) | RunnableLambda(
    lambda value: value["missing"]
)
try:
    bad.invoke({"text": "hello"})
except Exception as error:
    print(type(error).__name__, error)

good = RunnablePassthrough.assign(
    normalized=RunnableLambda(lambda value: value["text"].strip())
) | RunnableParallel(
    text=RunnableLambda(lambda value: value["normalized"]),
    length=RunnableLambda(lambda value: len(value["normalized"])),
)
print(good.invoke({"text": " hello "}))
```

观察失败发生在哪一个组件，再给每个节点写出“输入类型 -> 输出类型”。这是以后排查 Agent 工具结果、消息协议和 Graph State 错误的基本方法。

## 22. 进阶自测

1. 为什么 Parallel 分支之间默认不能共享中间字段？
2. 为什么 `max_concurrency` 不是数据库事务或权限机制？
3. 哪类异常可以重试，哪类异常应转入状态查询？
4. 如果链路中间需要人工审批，为什么不建议只靠 Runnable 解决？
5. 如何替换真实模型来测试 Prompt 和 Parser，而不消耗 API 费用？

## 23. 官方资料

- [LangChain Runnable Concepts](https://docs.langchain.com/oss/python/langchain/runnables)
- [Runnable API Reference](https://reference.langchain.com/python/langchain-core/runnables/Runnable)
- [RunnableLambda API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnableLambda)
- [RunnableParallel API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnableParallel)
- [RunnableBranch API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnableBranch)
- [RunnablePassthrough API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnablePassthrough)

> 本课代码基于 Python 3.11、`langchain==1.3.14`、`langchain-core==1.4.9` 验证。具体模型是否支持批量、流式和异步能力，仍需使用目标供应商做集成测试。
