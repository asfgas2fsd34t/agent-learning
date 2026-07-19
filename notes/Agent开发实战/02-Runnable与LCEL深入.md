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

实践目录：[practice/06-langchain-runnables](../../practice/06-langchain-runnables/README.md)

```powershell
cd practice/06-langchain-runnables
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

## 16. 官方资料

- [LangChain Runnable Concepts](https://docs.langchain.com/oss/python/langchain/runnables)
- [Runnable API Reference](https://reference.langchain.com/python/langchain-core/runnables/Runnable)
- [RunnableLambda API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnableLambda)
- [RunnableParallel API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnableParallel)
- [RunnableBranch API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnableBranch)
- [RunnablePassthrough API Reference](https://reference.langchain.com/python/langchain-core/runnables/RunnablePassthrough)

> 本课代码基于 Python 3.11、`langchain==1.3.14`、`langchain-core==1.4.9` 验证。具体模型是否支持批量、流式和异步能力，仍需使用目标供应商做集成测试。

