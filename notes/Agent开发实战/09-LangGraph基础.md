# 09 LangGraph 基础

> 学习目标：不仅会调用 `StateGraph`，还要能解释一次图执行时状态如何流动、节点返回值如何合并、边如何决定下一步，以及怎样测试和定位问题。

## 1. 为什么需要 Graph

线性 LCEL Chain 适合固定顺序的处理；Agent 和业务流程经常有状态、分支、循环、暂停和恢复。LangGraph 把这些控制流显式写出来：

```text
State：流程共享的数据协议
Node：读取 State 并返回增量更新
Edge：决定下一个 Node
START/END：图的入口和终点
compile：把定义检查并转换为可执行图
```

图不是“让模型自动规划一切”，而是让开发者把高风险的流程边界固定下来，模型只在被允许的节点内决策。

### 1.1 Graph 解决的是控制流问题

大模型擅长理解自然语言和做模糊判断，但不擅长可靠地维护业务流程。比如一个 BI 分析任务可能要求：

```text
校验用户权限 -> 理解指标 -> 查询数据 -> 判断是否需要下钻
                                   | 是 -> 查询维度明细 -> 重新判断
                                   | 否 -> 生成结论 -> 人工确认
```

如果把整个流程只写在 Prompt 中，模型需要同时记住当前执行到哪、已经查询过什么、还剩多少预算、失败后能否重试。流程越长，这些约束越容易丢失。LangGraph 的作用是把这些信息从 Prompt 中拿出来，变成程序可以检查的 State 和 Edge。

因此需要区分两类决策：

- **业务流程决策**：是否允许查数据、最多重试几次、写操作是否需要审批。这些应由代码和图控制。
- **语义决策**：用户问的是哪个指标、检索结果是否相关、报告怎样表达。这些可以交给模型。

Graph 并不会让模型更聪明，它让模型参与的流程更可控。

### 1.2 一次 invoke 到底发生了什么

以练习中的 `plan -> write` 为例：

```text
1. graph.invoke({"topic": "Runnable"}) 创建本次运行的初始 State
2. START 把执行权交给 plan
3. plan 读取 topic，返回 {"outline": [...]}
4. 运行时把该增量合并进 State
5. 普通 Edge 把执行权交给 write
6. write 读取 topic 和 outline，返回 {"draft": "..."}
7. 运行时再次合并 State
8. write -> END，返回最终 State
```

可以把它理解为下面的循环：

```python
state = initial_input
current_node = "plan"

while current_node != END:
    update = run_node(current_node, state)
    state = merge(state, update)
    current_node = choose_next_node(current_node, state)

return state
```

这段伪代码揭示了 LangGraph 最重要的四个问题：

1. 节点能读取哪些字段？
2. 节点允许更新哪些字段？
3. 更新与旧状态怎样合并？
4. 合并后的状态会被路由到哪里？

真正的工程问题通常都发生在这四个位置，而不是 `add_node` 这行 API 上。

## 2. State 是运行时公共协议

```python
class State(TypedDict, total=False):
    topic: str
    outline: list[str]
    draft: str
```

节点接收完整的当前 State，通常只返回自己负责更新的字段：

```python
def plan_node(state: State) -> dict:
    return {"outline": ["定义", "流程", "边界"]}
```

这不是把整份 State 重新返回一遍。增量更新可以减少覆盖其他节点结果的风险，也便于检查每一步到底改变了什么。

### State、消息和配置不是一回事

```text
State：业务流程和中间结果
messages：对话和工具协议的一部分
config.thread_id：恢复和隔离的运行标识
```

不要把所有变量都追加到 `messages`，也不要把用户可修改的内容放进租户隔离依据。

### 2.1 State 是节点之间的接口，不是随手使用的字典

State 看起来只是一个 Python 字典，但设计时应把它当成模块间的 API。每个字段都要回答：

| 字段 | 谁写入 | 谁读取 | 是否必填 | 合并方式 |
|---|---|---|---|---|
| `topic` | 调用方 | `plan`、`write` | 输入时必填 | 覆盖 |
| `outline` | `plan` | `write` | `write` 前必填 | 覆盖 |
| `draft` | `write` | 调用方 | 成功结束时必填 | 覆盖 |

练习中使用 `total=False`，表示类型层面允许字段暂时不存在。这符合图的执行过程：初始状态只有 `topic`，`outline` 和 `draft` 是后续逐步产生的。但它也意味着下面的代码可能在运行时失败：

```python
outline = state["outline"]  # plan 未执行或执行失败时会触发 KeyError
```

因此 `total=False` 不是“所有字段都可有可无”，而是“字段在不同执行阶段逐步变为可用”。开发者仍需定义每个节点的前置条件。

### 2.2 输入、内部状态和输出可以分开建模

小练习用一个 State 足够，生产流程通常要区分三类协议：

```python
class GraphInput(TypedDict):
    topic: str


class GraphState(TypedDict, total=False):
    topic: str
    outline: list[str]
    draft: str
    status: str


class GraphOutput(TypedDict):
    draft: str
    status: str
```

这样做有三个好处：

1. 调用方不需要知道 `attempts`、`route` 等内部实现字段。
2. 内部敏感信息不会意外返回给客户端。
3. 重构内部流程时，外部输入输出契约可以保持稳定。

是否采用独立 Schema 取决于 LangGraph 版本和流程复杂度，但“外部契约不等于内部状态”这个设计原则始终成立。

### 2.3 TypedDict 与 Pydantic 的选择

`TypedDict` 主要服务于静态类型检查，本身不会在运行时验证数据：

```python
input_state: State = {"topic": 123}  # Python 运行时仍然能构造出来
```

Pydantic 模型可以在运行时校验类型、范围和格式，适合边界输入：

```python
from pydantic import BaseModel, Field


class Request(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
```

常见工程做法是：

```text
HTTP/API 输入 -> Pydantic 校验 -> 转成 Graph State
Graph 内部节点 -> TypedDict 传递轻量状态
Graph 输出 -> 响应模型过滤和校验
```

类型校验不能代替权限校验。`region: str` 合法，不代表当前用户有权查询这个区域。

### 2.4 字段所有权

每个普通字段最好只有一个主要写入者。例如 `plan` 负责 `outline`，`write` 负责 `draft`。如果多个节点都可以随意重写 `status`、`question` 或 `answer`，调试时很难判断最终值来自哪里。

推荐把状态分成三类：

- **事实字段**：原始问题、用户身份、查询结果。修改要非常谨慎。
- **过程字段**：当前步骤、尝试次数、预算消耗。由程序维护，不交给模型自由生成。
- **产物字段**：提纲、分析结论、最终答案。可以由模型生成，但需要校验。

尤其不要让模型直接控制 `attempts`、`approved`、`tenant_id`、`max_budget` 等安全或终止字段。

## 3. Reducer：多个更新如何合并

普通字段通常是“后一次更新覆盖前一次”。如果并行节点都要追加结果，需要显式 reducer：

```python
import operator
from typing import Annotated, TypedDict


class ParallelState(TypedDict, total=False):
    findings: Annotated[list[str], operator.add]
```

没有 reducer 时，两个节点同时写 `findings` 可能发生冲突或丢数据。Reducer 只定义合并方式，不自动解决重复、顺序、事务和权限问题；这些仍要在节点或服务层处理。

### 3.1 覆盖和追加是两种不同语义

没有 reducer 的普通字段通常使用“后一次更新覆盖旧值”的语义：

```text
旧状态：{"draft": "v1"}
节点更新：{"draft": "v2"}
新状态：{"draft": "v2"}
```

带 `operator.add` 的列表字段使用追加语义：

```text
旧状态：{"findings": ["华东下降"]}
节点更新：{"findings": ["家电下降"]}
新状态：{"findings": ["华东下降", "家电下降"]}
```

Reducer 的本质是给字段定义 `old_value + update -> new_value` 的规则。它不只为并行服务，循环中的多次更新也会使用相同的合并规则。

### 3.2 Reducer 必须满足可预测性

并行执行时，不要默认分支完成顺序固定。自定义 reducer 最好考虑：

- **结合律**：不同分组方式合并，结果是否一致。
- **顺序依赖**：A 后 B 与 B 后 A 是否产生不同业务含义。
- **幂等性**：同一个更新重复到达，是否会产生重复数据。
- **可序列化**：结果能否被 checkpoint 保存和恢复。

例如直接追加列表保留了所有结果，但不能自动去重，也不保证业务展示顺序。BI 多维分析可以先追加结构化结果，再在 merge 节点中稳定排序：

```python
class Finding(TypedDict):
    dimension: str
    conclusion: str


def merge_node(state: ParallelState) -> dict[str, object]:
    ordered = sorted(state["findings"], key=lambda item: item["dimension"])
    return {"ordered_findings": ordered}
```

不要在 reducer 中调用数据库、模型或外部接口。Reducer 可能在状态重放和并发合并时执行，应保持纯函数特征。

## 4. Node：图中的计算单元

节点可以是普通函数、异步函数、Runnable、工具或子图。无论形式是什么，都应遵守同一个核心契约：

```text
读取当前 State -> 执行一个职责 -> 返回状态增量
```

练习的 `plan_node` 是确定性节点，输入相同就会返回相同结果；`write_node` 内部调用 writer，是非确定性节点，可能受模型、网络和限流影响。

### 4.1 节点应该保持单一职责

不推荐把“检索、生成、保存数据库、发送通知”全部塞进一个节点。大节点会导致：

- 无法判断失败发生在哪一步。
- 只能整体重试，可能重复执行已经成功的副作用。
- 测试必须同时模拟多个外部依赖。
- 无法在中间步骤增加审核或路由。

更合理的拆分是：

```text
retrieve -> generate -> validate -> persist -> notify
```

但也不要把每一行代码都拆成节点。节点边界通常放在“需要独立观测、重试、路由、缓存或审批”的位置。

### 4.2 依赖注入让图可测试

练习不是在 `write_node` 中直接创建 `ChatOpenAI`，而是让 `build_graph(writer)` 接收函数：

```python
def build_graph(writer: Callable[[str], str]):
    ...
```

测试时可以传入：

```python
lambda prompt: f"收到：{prompt}"
```

这样单元测试验证的是图结构和数据流，不依赖 API Key、网络和模型输出。真实模型只在 `main()` 这个应用入口中组装进去。这个模式同样适用于数据库查询器、向量检索器和业务工具。

### 4.3 副作用、幂等和重试

读取数据库通常可以安全重试，创建订单、发邮件、扣款等写操作则不能盲目重试。因为节点可能已经成功执行外部操作，只是在返回结果前发生网络超时。

写操作节点应考虑：

```text
idempotency_key：同一业务请求重复执行时返回同一结果
operation_id：记录外部操作编号，便于查询真实状态
status query：结果未知时先查状态，而不是再次写入
```

幂等不是 LangGraph 自动提供的。Graph 可以决定什么时候重试，但业务服务必须保证重试不会产生重复副作用。

### 4.4 节点异常怎样传播

如果节点直接抛出异常且没有配置相应处理，本次图执行会在该节点停止，`invoke()` 向调用方抛出异常，后续边不会执行。

有两种常见错误处理方式：

```text
技术异常：网络断开、程序 bug、依赖不可用 -> 抛异常，由外层重试和监控处理
业务结果：无权限、参数不合法、没有数据 -> 写入结构化状态，由条件边路由
```

不要把所有异常都吞掉后返回空字符串。空字符串无法区分“确实没有数据”和“查询系统故障”，会让模型基于错误前提生成结论。

## 5. Builder 到 Compiled Graph

```python
builder = StateGraph(State)
builder.add_node("plan", plan_node)
builder.add_node("write", write_node)
builder.add_edge(START, "plan")
builder.add_edge("plan", "write")
builder.add_edge("write", END)
graph = builder.compile()
```

`StateGraph` builder 是声明阶段，`compile()` 会把节点、边和状态规则组装成可执行对象，并检查部分结构错误。编译后的图实现 Runnable 风格的 `invoke`、`stream`、`ainvoke`；编译不是执行，真正运行仍从 `graph.invoke(input)` 开始。

### 5.1 声明、编译和执行是三个阶段

```text
声明：add_node / add_edge / add_conditional_edges
编译：compile() 生成可执行图，可在此配置 checkpointer 等运行能力
执行：invoke / ainvoke / stream 接收某一次任务的输入和配置
```

`builder` 更像流程定义器；`graph` 才是可以调用的 Runnable。通常应用启动时构建并编译一次图，请求到来后重复调用编译结果，而不是每个请求都重新搭图。

`compile()` 能发现部分结构问题，例如入口和边配置问题，但不能证明所有业务路径正确。路由返回非法值、节点漏写字段、权限判断错误仍要通过测试和运行时校验发现。

### 5.2 invoke、ainvoke 和 stream

同步程序可以使用：

```python
result = graph.invoke({"topic": "Runnable"})
```

异步 Web 服务通常使用：

```python
result = await graph.ainvoke({"topic": "Runnable"})
```

需要展示进度或观测节点更新时可以使用流式执行：

```python
for event in graph.stream(
    {"topic": "Runnable"},
    stream_mode="updates",
):
    print(event)
```

`stream_mode="updates"` 关注每个步骤产生的增量，适合回答“哪个节点写入了这个字段”；完整状态流则适合观察每一步合并后的 State。具体支持的 stream mode 应以项目安装的 LangGraph 版本为准。

流式返回不代表节点内部的模型一定在逐 token 输出。图的步骤流和模型 token 流是两个层次，需要分别配置。

## 6. Edge 的执行语义

- 普通 edge：节点成功后固定进入下一个节点。
- Conditional edge：调用路由函数，根据当前 State 选择目标。
- `END`：流程结束并返回最终 State。

路由函数只负责返回“去哪”，不要在路由函数里调用数据库或模型。这样路由可以被单元测试，副作用也不会因为路由重算而重复发生。

### 6.1 普通 Edge 表示确定性顺序

```python
builder.add_edge("plan", "write")
```

这句话表达的是：`plan` 成功完成并合并状态后，下一步一定执行 `write`。它不是 Python 函数内部的直接调用，因此运行时可以在两个节点之间记录状态、输出流事件，配置持久化后还可以在步骤边界保存 checkpoint。

### 6.2 Conditional Edge 表示基于状态选择路径

```python
from typing import Literal


def route_after_check(state: State) -> Literal["write", "reject"]:
    return "write" if state.get("outline") else "reject"


builder.add_conditional_edges(
    "check",
    route_after_check,
    {"write": "write", "reject": "reject"},
)
```

路由函数的输出是一个有限集合中的标签。使用 `Literal` 能让 IDE 和类型检查器知道合法值，但运行时仍应测试非法路径。

为什么不直接在路由函数里生成文本或查数据库？因为路由函数的职责应当接近纯函数：同一份 State 应得到同一个路径。副作用藏在路由里会造成执行日志看不到、重复求值时重复调用、失败无法单独重试。

### 6.3 START 和 END 不是普通业务节点

`START` 是虚拟入口，用于说明初始输入首先流向哪里；`END` 是虚拟终点，表示本次执行完成。它们不执行模型或业务函数。

到达 `END` 只表示图的控制流结束，不自动表示业务成功。最终状态可能是：

```python
{"status": "unknown", "answer": "当前证据不足"}
```

因此业务成功与否应看结构化 `status`，不能只看 `invoke()` 是否正常返回。

## 7. practice/08 的数据流

对应代码：[practice/Agent开发实战/08-langgraph-basics](../../practice/Agent开发实战/08-langgraph-basics/README.md)

```text
输入 {topic}
 -> plan_node 写入 outline
 -> write_node 读取 topic + outline，调用 writer
 -> 写入 draft
 -> END 返回完整 State
```

练习把 writer 作为函数注入，所以测试可以用假实现，不需要真实模型。这是一个值得保留的工程习惯：把模型调用和图结构分开，先测试控制流，再做集成测试。

### 7.1 逐步观察 State

初始输入：

```python
{"topic": "Runnable"}
```

`plan_node` 返回的不是最终结果，而是状态增量：

```python
{
    "outline": [
        "Runnable 的定义",
        "Runnable 的工作流程",
        "Runnable 的边界",
    ]
}
```

合并后，`write_node` 实际看到的是：

```python
{
    "topic": "Runnable",
    "outline": [
        "Runnable 的定义",
        "Runnable 的工作流程",
        "Runnable 的边界",
    ],
}
```

`write_node` 将 State 转成 writer 所需的字符串协议。writer 返回文本后，节点再把它包装成：

```python
{"draft": "模型或假 writer 返回的内容"}
```

最终返回值包含 `topic`、`outline` 和 `draft`，因为 `invoke()` 默认返回合并后的最终状态，而不是只返回最后一个节点的增量。

### 7.2 为什么模型在 main 中创建

`create_model()` 读取环境变量并创建 `ChatOpenAI`；`build_graph()` 只依赖一个可调用的 writer。它们分开后：

```text
图结构测试：使用假 writer，快速、稳定、无费用
模型适配测试：单独验证 ChatOpenAI 的配置和响应解析
端到端测试：少量调用真实模型，验证整体集成
```

这比所有测试都调用真实模型更可靠。真实模型输出具有随机性，外部 API 也可能限流，不能作为控制流单元测试的唯一依据。

## 8. 测试 Graph 的三个层次

### 8.1 节点单元测试

如果节点逻辑复杂，最好把它定义在可直接导入的位置，传入最小 State，断言返回的增量：

```python
update = plan_node({"topic": "Runnable"})
assert update["outline"][0] == "Runnable 的定义"
```

重点测试输入缺失、空值、外部依赖失败和返回格式异常。

### 8.2 图控制流测试

当前练习中的测试属于这一层：

```python
graph = build_graph(lambda prompt: f"收到：{prompt}")
result = graph.invoke({"topic": "Runnable"})

self.assertEqual(len(result["outline"]), 3)
self.assertIn("Runnable", result["draft"])
```

它同时证明 `plan` 的结果传给了 `write`，并且最终状态被正确返回。进阶图还需要为每条条件分支和循环终止条件各写一个测试。

### 8.3 集成和失败测试

生产图至少应覆盖：

- 模型超时后是抛异常、重试还是进入 fallback。
- 节点返回缺失字段时，下游是否暴露清晰错误。
- 权限拒绝是否确保查询节点没有被调用。
- 循环是否在最大次数、超时或预算耗尽时终止。
- 写操作返回未知状态时是否避免重复执行。

不能只测试“成功生成了字符串”。Graph 最有价值的部分正是失败路径和控制流。

## 9. 可执行实验

1. 在 `plan_node` 返回未知字段，观察编译或执行时的行为。
2. 让 `writer` 抛出异常，记录图在哪一步停止。
3. 给 State 增加 `status`，让每个节点只更新自己负责的状态。
4. 用 `graph.stream(..., stream_mode="updates")` 观察每个节点的增量更新。

推荐按以下顺序实际修改练习，每次只改一个点并运行测试：

1. 在 writer 中打印收到的 Prompt，确认 State 到模型输入的转换过程。
2. 给 State 增加 `draft_length`，由 `write_node` 与 `draft` 一起返回。
3. 增加 `validate` 节点，草稿为空时写入 `status="failed"`，否则写入 `status="completed"`。
4. 把 `write -> END` 改成 `write -> validate -> END`，用 stream 观察三个节点更新。
5. 模拟 writer 抛出 `TimeoutError`，确认异常没有被误认为空结果。

## 10. LangGraph、Chain 与 Agent 的取舍

```text
固定输入 -> 固定输出 -> 固定顺序：LCEL Chain
模型选择工具：Agent
多节点状态、循环、恢复和人工介入：LangGraph
```

LangGraph 不是所有函数的替代品。图越大，State 和边越难维护；只有在控制流或恢复语义确实需要显式建模时才引入它。

三者不是互斥关系：

```text
Chain 可以作为一个 Node
Tool-calling Agent 可以作为一个 Node
Graph 可以组织多个 Chain、Agent 和普通函数
```

选择的关键不是任务听起来是否“智能”，而是控制权在哪里：

| 场景 | 更适合 | 原因 |
|---|---|---|
| 文本总结、分类、结构化抽取 | 单次模型或 Chain | 固定输入输出，不需要持久状态 |
| 模型从多个工具中自主选择 | Agent | 下一步取决于模型的语义决策 |
| 固定审批流程、分支、循环、恢复 | Graph | 业务需要显式控制路径和状态 |
| 长任务中局部需要自主查工具 | Graph + Agent Node | 全局流程由 Graph 控制，局部交给 Agent |

Graph 也不是传统工作流引擎、数据库事务或消息队列的替代品。跨系统的强一致事务、超长定时任务和海量事件处理，仍需要相应基础设施配合。

## 11. 常见误区

### 误区一：State 里字段越多越方便

字段越多，节点耦合越强，checkpoint 越大，敏感信息泄露面也越大。只保留流程恢复和后续决策真正需要的数据，大对象可以保存引用或业务 ID。

### 误区二：节点返回完整 State 更清晰

返回完整 State 容易用旧值覆盖其他节点刚写入的数据。默认返回自己负责的增量；只有明确需要替换字段时才返回该字段。

### 误区三：到达 END 就是成功

END 只表示执行结束。`completed`、`unknown`、`forbidden`、`failed` 等业务状态必须单独建模。

### 误区四：用了 Graph 就自动拥有长期记忆

State 是本次运行的数据协议；checkpoint 用于保存执行状态；跨会话长期记忆通常还需要独立存储和检索策略。三者不能混为一谈。

## 12. 自测

1. 为什么 Node 应返回增量字段而不是随意返回值？
2. 普通字段和带 reducer 的字段合并行为有什么区别？
3. `compile()` 和 `invoke()` 分别完成什么工作？
4. 为什么路由函数不应直接执行副作用？
5. 什么时候 Chain 比 Graph 更合适？
6. `total=False` 为什么不代表节点可以随意忽略必需字段？
7. 为什么写操作节点的幂等性不能由 LangGraph 自动保证？
8. `stream_mode="updates"` 最适合排查哪类问题？
9. 到达 `END` 后，为什么仍可能是业务失败？
10. 为什么外部输入和内部 State 最好不要永远使用同一个 Schema？

## 官方资料

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
