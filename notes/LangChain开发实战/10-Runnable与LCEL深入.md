# 10 Runnable 与 LCEL 深入

> 本篇提取自原有 Runnable 学习笔记，补充课件 01-09 没有系统展开的 LangChain 组合协议。

## 学习目标

- 理解 Runnable 是 LangChain 接口而不是 Python 原生类型
- 看懂 `|` 如何构造 `RunnableSequence`
- 掌握 Lambda、Parallel、Passthrough、Assign 和 Branch
- 理解 `invoke()` 的实际执行链路
- 掌握 Batch、Stream、Async、Config、Retry 和 Fallback
- 建立 Runnable 的测试与边界意识

## 1. Runnable 是什么

Runnable 是 LangChain 定义的统一执行协议。模型、Prompt、Parser 和许多组合组件都实现了它。

```text
invoke(input)
ainvoke(input)
batch(inputs)
abatch(inputs)
stream(input)
astream(input)
```

Runnable 不是 Python 标准库类。它使用 Python 泛型表达输入输出类型：

```python
Runnable[Input, Output]
```

这和 Java 泛型在“描述类型关系”上类似，但 Python 类型标注默认不等于运行时强校验。

## 2. Runnable 的核心契约

每个 Runnable 都可以理解为：

```text
Input -> 执行逻辑 -> Output
```

组合能否成功取决于相邻组件的数据契约：

```text
A: dict -> ChatPromptValue
B: ChatPromptValue -> AIMessage
C: AIMessage -> str

A | B | C 合法
```

如果上一段输出 `dict`，下一段却只接受字符串，链会在运行时失败。

## 3. `|` 与 `RunnableSequence`

```python
chain = prompt | model | parser
```

`|` 在 Python 中调用对象的 `__or__`，LangChain 使用它构造 `RunnableSequence`。此时只是组装，没有调用模型。

```text
定义 chain：构建执行结构
chain.invoke：真正开始运行
```

等价理解：

```python
from langchain_core.runnables import RunnableSequence

chain = RunnableSequence(prompt, model, parser)
```

### 3.1 `invoke()` 的执行链路

```text
chain.invoke(user_input, config)
-> Sequence 接收输入
-> 调用 prompt.invoke(user_input, child_config)
-> 把 PromptValue 交给 model.invoke(...)
-> 把 AIMessage 交给 parser.invoke(...)
-> 返回最终结果
```

Config、Callback、Tag 和 Trace 会沿组合链向下传播，每个组件形成独立子运行记录。

## 4. `RunnableLambda`

普通函数没有 `.invoke()`。使用 `RunnableLambda` 可以把函数适配为 Runnable：

```python
from langchain_core.runnables import RunnableLambda


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


normalize = RunnableLambda(normalize_text)
result = normalize.invoke("  hello   world  ")
```

内部可以理解为适配器：

```text
RunnableLambda.invoke(input)
-> 调用原函数(input)
-> 获取函数返回值
-> 接入 Config、Callback、Batch 和 Async 协议
```

它没有把函数“编译成另一种语言”，只是用 Runnable 接口包装调用。

### 4.1 `@chain` 装饰器

```python
from langchain_core.runnables import chain


@chain
def clean_text(value: str) -> str:
    return value.strip().lower()
```

装饰后 `clean_text` 是 Runnable。简单函数可以使用 `@chain`，需要显式命名、配置或复用函数对象时可以使用 `RunnableLambda`。

### 4.2 适用边界

适合包装：

- 数据格式转换
- 短小的确定性规则
- 调用已有 Service
- 为非 Runnable 组件增加统一接口

不适合把大量业务逻辑堆进一个 Lambda。复杂逻辑应提取为可独立测试的模块。

## 5. `RunnableParallel`

同一个输入同时交给多个 Runnable，最后返回字典：

```python
from langchain_core.runnables import RunnableLambda, RunnableParallel


def normalize_text(value: str) -> str:
    return value.strip().lower()


def text_length(value: str) -> int:
    return len(value)


features = RunnableParallel(
    normalized_text=RunnableLambda(normalize_text),
    text_length=RunnableLambda(text_length),
)

result = features.invoke("  LangChain  ")
```

返回：

```python
{
    "normalized_text": "langchain",
    "text_length": 13,
}
```

每个分支收到的是同一个原始输入。分支之间不共享可变状态，也不能依赖另一个并行分支先完成。

### 5.1 并行的边界

适合并行：

- 互不依赖的特征提取
- 多路只读查询
- 多模型候选生成

不适合直接并行：

- 有执行顺序的写操作
- 修改同一业务资源
- 一个分支依赖另一个分支结果

## 6. `RunnablePassthrough`

Passthrough 原样返回输入：

```python
from langchain_core.runnables import RunnablePassthrough

same = RunnablePassthrough()
assert same.invoke({"text": "hello"}) == {"text": "hello"}
```

### 6.1 `assign()`

`assign()` 要求输入是字典，并在保留原字段的同时计算新字段：

```python
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

feature_runnables = RunnableParallel(
    normalized_text=RunnableLambda(lambda value: value["text"].strip()),
    text_length=RunnableLambda(lambda value: len(value["text"])),
)

pipeline = RunnablePassthrough.assign(features=feature_runnables)

result = pipeline.invoke({"text": "  hello  ", "source": "user"})
```

返回：

```python
{
    "text": "  hello  ",
    "source": "user",
    "features": {
        "normalized_text": "hello",
        "text_length": 9,
    },
}
```

可以理解为：

```python
{
    **original_input,
    "features": feature_runnables.invoke(original_input),
}
```

`assign()` 不会只返回新增字段，而是返回“原字典 + 新字段”。

## 7. `RunnableBranch`

根据输入选择一条分支：

```python
from langchain_core.runnables import RunnableBranch

branch = RunnableBranch(
    (lambda value: value["text_length"] > 80, long_chain),
    short_chain,
)
```

`value` 来自上一个 Runnable 的输出：

```text
上游输出 dict
-> RunnableBranch 接收该 dict
-> 依次执行条件函数(value)
-> 第一个 True 对应的 Runnable 被执行
-> 都不匹配时执行最后的默认 Runnable
```

完整示例：

```python
prepare = RunnableLambda(
    lambda text: {
        "text": text,
        "text_length": len(text),
    }
)

chain = prepare | RunnableBranch(
    (lambda value: value["text_length"] > 80, long_chain),
    short_chain,
)
```

条件函数应保持确定性、快速且无副作用。复杂业务路由不应只依赖模型自然语言判断。

## 8. 字典在 LCEL 中的含义

在 Python 中：

```python
{"a", "b"}          # set
{"a": 1, "b": 2}  # dict
```

LCEL 中管道右侧出现字典时，LangChain 通常会把它转换为 `RunnableParallel`：

```python
chain = source | {
    "summary": summary_chain,
    "keywords": keyword_chain,
}
```

等价理解：

```python
chain = source | RunnableParallel(
    summary=summary_chain,
    keywords=keyword_chain,
)
```

## 9. 字典拆分与合并

字典推导式：

```python
original = {
    key: item
    for key, item in value.items()
    if key != "features"
}
```

含义是遍历 `value`，复制除 `features` 之外的键值。

字典解包：

```python
merged = {**original, **features}
```

后面的字典键冲突时覆盖前面的值：

```python
{**{"a": 1}, **{"a": 2}} == {"a": 2}
```

这类操作常用于把 Parallel 或 Assign 产生的嵌套结构整理为下游需要的输入。

## 10. 单次与批量

### 10.1 `invoke`

```python
result = chain.invoke(single_input)
```

一次输入对应一次输出。

### 10.2 `batch`

```python
results = chain.batch([input_a, input_b, input_c])
```

对多个独立输入执行同一 Runnable，结果顺序与输入顺序一致。

```text
single：一个 Case 走一次完整链
batch：多个 Case 分别走完整链
```

Batch 不是把多个输入拼成一个 Prompt。默认实现可能使用线程并发，不代表模型提供商拥有真正的批量 API。

### 10.3 并发限制

```python
results = chain.batch(
    inputs,
    config={"max_concurrency": 4},
)
```

要同时考虑提供商限流、数据库连接数和下游 API 容量。

## 11. 异步调用

```python
result = await chain.ainvoke(input_data)
results = await chain.abatch(inputs)
```

异步适合网络 I/O 密集场景。它不会让一次模型推理本身更快，而是提高等待期间的并发利用率。

如果 RunnableLambda 内部执行阻塞数据库或 HTTP 调用，应使用异步客户端或在线程池中受控执行，不能阻塞事件循环。

## 12. 流式调用

```python
for chunk in chain.stream(input_data):
    print(chunk, end="")
```

是否能逐 Token 流式输出取决于链中每个组件是否支持流式转换。如果中间某一步必须读取完整输入才能继续，流式可能在该位置缓冲。

典型阻塞点：

- 普通函数等待完整上游文本
- Pydantic Parser 等完整 JSON 后才能解析
- 聚合所有结果后再排序

流式设计要区分：

```text
模型 Token 流
Runnable 中间结果流
Agent 状态事件流
业务进度事件
```

## 13. Runnable Config

```python
config = {
    "run_name": "build_study_note",
    "tags": ["learning", "lcel"],
    "metadata": {
        "scenario": "summary",
    },
    "max_concurrency": 4,
}

result = chain.invoke(input_data, config=config)
```

Config 与业务输入不同：

```text
input：参与业务计算的数据
config：追踪、回调、并发和运行配置
state：跨节点持续变化的任务状态
```

不要把 `user_id`、金额等业务参数藏进 Metadata 后再作为业务事实使用。

## 14. 重试

```python
reliable_chain = chain.with_retry(
    stop_after_attempt=3,
)
```

重试应只覆盖临时错误：

- 网络短暂失败
- 限流
- 提供商 5xx

不应重试：

- Schema 固定不匹配
- 权限失败
- 参数错误
- 确定性业务拒绝

把整个 Chain 重试可能重复执行前面的写操作。应把重试放在最小、安全、幂等的 Runnable 上。

## 15. Fallback

```python
chain_with_fallback = primary_chain.with_fallbacks(
    [backup_chain]
)
```

Fallback 可以切换模型或策略，但输入输出协议必须一致：

```text
Primary: Input -> StudyNote
Fallback: Input -> StudyNote
```

如果备用链只返回字符串，下游却要求 Pydantic 对象，Fallback 成功后仍会在后续失败。

## 16. 错误传播

Sequence 默认遇到异常就停止，后续步骤不执行：

```text
A 成功 -> B 失败 -> C 不执行
```

Parallel 中一个分支失败，默认可能使整体失败。业务需要部分成功时，应让每个分支返回稳定结果：

```python
{
    "ok": False,
    "data": None,
    "error_code": "SEARCH_TIMEOUT",
}
```

但不要把编程错误全部吞掉伪装成业务失败。

## 17. 自定义 Runnable

多数情况下不需要继承 Runnable：

```text
已有 Python 函数 -> RunnableLambda
多个组件顺序执行 -> RunnableSequence / `|`
并行执行 -> RunnableParallel
条件分支 -> RunnableBranch
```

只有在以下情况才考虑自定义类：

- 需要特殊的 Stream 实现
- 需要统一管理资源生命周期
- 需要提供配置 Schema
- 需要框架级复用和序列化
- Lambda 无法清楚表达复杂组件行为

自定义时必须明确同步、异步、批量、流式和 Config 的行为，成本明显高于包装函数。

## 18. 测试策略

### 18.1 组件测试

```python
def test_normalize_text() -> None:
    assert normalize_text("  A   B ") == "A B"
```

### 18.2 Runnable 单次测试

```python
def test_feature_pipeline_single() -> None:
    result = feature_pipeline.invoke({"text": "hello"})
    assert result["features"]["text_length"] == 5
```

### 18.3 批量测试

```python
def test_feature_pipeline_batch() -> None:
    results = feature_pipeline.batch(
        [{"text": "a"}, {"text": "abcd"}]
    )
    assert [item["features"]["text_length"] for item in results] == [1, 4]
```

### 18.4 分支覆盖

至少准备一个短文本和一个超过阈值的长文本，确认两个分支都执行。不要让测试数据全部落入同一分支。

### 18.5 端到端测试

真实模型测试负责验证 Prompt、模型能力、Structured Output 和提供商兼容性。确定性数据转换仍应使用快速单元测试。

## 19. Runnable、Tool 和 Agent 的边界

| 组件 | 谁决定执行顺序 | 适合场景 |
|---|---|---|
| Runnable / LCEL | 程序员预先定义 | 确定性数据流 |
| Tool | 模型提出调用，应用执行 | 外部能力边界 |
| Agent | 模型根据状态动态选择下一步 | 开放式多步任务 |

能用固定 Runnable 完成的流程，不必为了“智能”改成 Agent。固定链更容易测试、预测成本和保证顺序。

## 20. 常见错误

### 20.1 上下游类型不匹配

先写清每一步输入输出，不要依赖运行时猜测。

### 20.2 Parallel 分支互相依赖

有依赖关系就改成 Sequence。

### 20.3 `assign()` 输入不是字典

先通过 Lambda 转换为字典，再使用 `assign()`。

### 20.4 对整个有副作用链重试

只在安全、幂等的最小组件上重试。

### 20.5 假设所有 Parser 都能流式

结构化解析常需要等待完整输出。

## 21. 自测

1. `|` 是在定义时执行模型，还是在 `invoke()` 时执行？
2. `RunnableParallel` 的每个分支收到什么输入？
3. `RunnablePassthrough.assign()` 返回什么？
4. `RunnableBranch` 中条件函数的 `value` 从哪里来？
5. `batch()` 与把多个问题拼成一个 Prompt 有什么区别？
6. 为什么整个 Chain 重试可能重复执行副作用？
7. 什么情况下才值得自定义 Runnable 类？

## 总结

```text
Runnable：LangChain 统一执行协议
RunnableSequence：按顺序传递输出
RunnableLambda：把函数适配为 Runnable
RunnableParallel：同一输入并行产生字典结果
RunnablePassthrough：保留原始输入
assign：原字典加新字段
RunnableBranch：按条件选择一个分支
Config：沿链传播的运行配置
Retry / Fallback：必须尊重副作用和类型契约
```

LCEL 适合表达程序员能够预先确定的数据流。理解 Runnable 后，Prompt、Model、Parser、Tool 和 Agent 的组合不再是黑盒。
