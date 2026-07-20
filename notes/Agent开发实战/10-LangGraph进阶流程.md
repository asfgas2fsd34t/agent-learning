# 10 LangGraph 进阶流程

> 学习目标：能够把复杂 Agent 设计成可终止、可恢复、可测试的状态机，并正确处理条件路由、循环、失败重试、并行合并和人工介入。

## 1. 先把控制流写成状态机

复杂 Agent 流程不是“加一个更强的 Prompt”就能稳定。先定义状态和合法路径：

```text
classify -> direct_answer -> END
        \-> retrieve -> evaluate
                         | enough -> answer -> END
                         | retry  -> rewrite -> retrieve
```

每条路径都应回答：输入是什么、输出更新什么、失败去哪、何时结束、是否可以重试。

### 1.1 先画状态转换，再写节点函数

状态机不是“画一个看起来像流程图的图”，而是定义有限的状态和合法转换。例如检索问答可以有：

```text
running + route=direct       -> answer
running + route=knowledge    -> retrieve
running + evidence=enough    -> answer
running + evidence=insufficient + attempts<2 -> rewrite
running + attempts>=2        -> unknown
forbidden                    -> END
failed                       -> END
completed                    -> END
```

设计时要区分：

- **节点名**：`retrieve`，表示接下来执行什么计算。
- **状态值**：`status="running"`，表示当前业务处于什么阶段。
- **路由标签**：`"rewrite"`，表示条件边选择哪条路径。

这三者可以同名，但概念不同。把它们混在一个字符串字段中，会导致节点既承担业务状态又承担流程跳转，后期很难扩展。

### 1.2 State 不变量

不变量是任何合法执行路径都必须满足的规则。例如：

```text
attempts >= 0
status=completed 时 answer 必须非空
status=forbidden 时不得存在 query_result
进入 answer 前 route 必须已经确定
每次 retrieve 后 attempts 必须增加 1
```

不变量比 Prompt 更可靠，因为可以在代码和测试中断言。可以增加一个校验节点，也可以在关键节点入口检查：

```python
def answer(state: State) -> dict[str, str]:
    if "route" not in state:
        raise ValueError("answer requires route")
    ...
```

对于权限、租户隔离和预算，校验必须放在真正执行工具的服务边界；图中的提前校验用于改善流程，但不能作为唯一防线。

## 2. 条件路由的契约

```python
builder.add_conditional_edges(
    "classify",
    lambda state: state["route"],
    {"knowledge": "retrieve", "direct": "answer"},
)
```

路由函数返回的是映射表中允许的标签，不是节点名也不是自然语言。让标签使用 `Literal` 或枚举，未知标签应在测试中失败，而不是静默走默认路径。

路由只读 State 并返回决策，不应修改 State。这样同一份状态可以重放，问题也可以定位为“分类错误”还是“节点执行错误”。

### 2.1 路由节点和路由函数的责任不同

练习中的 `classify` 节点负责计算并写入：

```python
{"route": "knowledge"}
```

条件边上的函数只读取这个字段：

```python
lambda state: state["route"]
```

这种拆分让分类结果进入 State 和执行日志。发生错误时可以回答：模型或规则是否分类错了，还是映射表配置错了。

另一种方式是直接让条件函数现场判断，但判断结果不会作为普通字段保留，复杂决策的可观测性会变差。简单的 `attempts >= 2` 判断适合直接放路由函数；需要模型调用、规则解释或审计的分类更适合独立节点。

### 2.2 Literal 只提供类型约束，不是运行时保险

```python
def after_retrieve(state: State) -> Literal["answer", "rewrite"]:
    ...
```

`Literal` 可以让类型检查器发现代码显式返回了错误标签，但 Python 默认不会在运行时验证函数真的遵守注解。模型生成的字符串更不能直接假设合法。

如果路由来自模型，应先做结构化解析和白名单映射：

```python
ALLOWED_ROUTES = {"direct", "knowledge"}


def normalize_route(raw_route: str) -> str:
    route = raw_route.strip().lower()
    if route not in ALLOWED_ROUTES:
        return "unknown"
    return route
```

不要让模型直接输出任意节点名。节点名属于内部控制结构，外部或模型只应提供有限的业务标签。

### 2.3 是否设置默认路径

默认路径有两种风险：

```text
未知标签 -> 默认执行查询：可能越权或增加费用
未知标签 -> 默认生成答案：可能在没有证据时编造
```

更安全的默认通常是进入明确的 `unknown`、`clarify` 或 `human_review` 节点，并记录原始标签。只有低风险场景才适合静默 fallback。

## 3. 循环必须有多个终止条件

检索改写循环至少需要：

```text
证据足够 -> answer
attempts >= MAX_ATTEMPTS -> answer/unknown
总超时或预算耗尽 -> stopped
重复 query/result -> stopped
不可重试错误 -> error
```

只在 Prompt 里说“不要无限循环”不可靠。`attempts` 应由程序递增，且 `MAX_ATTEMPTS` 是代码常量或可信配置，不接受模型修改。

练习 17 的 `retrieve` 每执行一次就增加 `attempts`，`after_retrieve` 在有 context 或尝试两次后进入 answer，否则进入 rewrite。这是最小的可控循环。

### 3.1 循环为什么比线性流程危险

线性图的最长步骤数由边的数量决定；带回边的图可能永远执行。下面任何情况都可能形成死循环：

- 改写后的 query 没有真正变化。
- 检索器稳定返回空结果。
- 模型一直判断证据不足。
- 计数器由模型生成，没有可靠递增。
- 错误被吞掉并转换为空结果，路由误以为可以继续检索。

因此每个循环都必须能在代码层回答“最坏情况下执行多少次、消耗多少时间和费用”。

### 3.2 终止条件应该是多维预算

只限制 `attempts` 还不够。生产流程常见预算包括：

```python
class State(TypedDict, total=False):
    attempts: int
    started_at: float
    tokens_used: int
    tool_calls: int
    seen_queries: list[str]
```

路由判断可以按优先级检查：

```text
1. 已获得足够证据 -> 正常结束
2. 不可重试错误 -> 失败结束
3. query 已重复 -> unknown，避免无效循环
4. attempts 达上限 -> unknown
5. 超过总耗时、token 或工具调用预算 -> budget_exceeded
6. 其他情况 -> rewrite/retry
```

预算字段必须由可信程序维护。模型可以建议“需要再查一次”，但不能自行提高 `max_attempts`。

### 3.3 计数时机要明确

练习在 `retrieve` 开始时增加 `attempts`，表示“已经发起了一次检索尝试”。如果只在成功后增加，连续超时可能永远不计数。

还要区分：

```text
attempts：当前逻辑步骤尝试次数
tool_calls：本次任务所有工具调用总数
replans：重新规划次数
```

三个计数器解决的问题不同。把它们都叫 retry_count 会掩盖任务实际消耗。

### 3.4 递归限制是最后一道保护，不是业务策略

LangGraph 运行时通常提供递归或步骤限制，用来阻止图无限执行。它适合作为兜底，但达到限制时往往以运行异常结束，用户得不到清晰的业务解释。

正确设计是先用 State 中的业务预算走向 `unknown` 或 `budget_exceeded`，再用运行时递归限制防御代码 bug。两层都要有，职责不同。

## 4. 错误状态要进入 State

不要让所有异常都表现成同一个 `Exception`。可以在 State 中建模：

```text
status: running | completed | unknown | forbidden | failed
error_code: INVALID_ARGUMENT | TIMEOUT | FORBIDDEN | UPSTREAM_ERROR | BUDGET_EXCEEDED | UNKNOWN
attempts: int
```

路由依据 `error_code` 决定是否重试。参数错误应返回用户修正；权限错误应停止；临时上游错误可在上限内重试；结果 unknown 需要查询状态或人工介入。

### 4.1 推荐的错误分类

| 错误码 | 含义 | 默认策略 | 能否原参数重试 |
|---|---|---|---|
| `INVALID_ARGUMENT` | 参数格式或业务取值非法 | 请求用户修正或重新构造参数 | 否 |
| `FORBIDDEN` | 用户没有执行权限 | 立即停止并审计 | 否 |
| `TIMEOUT` | 在规定时间内未得到确认结果 | 读操作可有限重试，写操作先查状态 | 视操作而定 |
| `UPSTREAM_ERROR` | 数据库、模型、检索服务异常 | 熔断、fallback 或有限重试 | 通常可以 |
| `BUDGET_EXCEEDED` | 步数、token、时间或费用超限 | 结束或人工确认追加预算 | 否 |
| `UNKNOWN` | 无法确认结果或证据不足 | 查询状态、澄清或人工介入 | 否 |

`UNKNOWN` 不等于 `UPSTREAM_ERROR`。前者表示当前系统无法确定事实，例如写请求已发出但响应丢失；后者表示已知依赖服务失败。处理方式不能相同。

### 4.2 错误信息既要给程序，也要给人

建议错误状态至少包含：

```python
class ErrorInfo(TypedDict):
    code: str
    message: str
    retryable: bool
    source: str
    operation_id: str | None
```

- `code` 供条件边做稳定路由。
- `message` 供日志和用户理解，但不能用于程序字符串匹配。
- `retryable` 是工具或服务根据错误类型给出的建议，不应完全由模型猜。
- `source` 帮助定位是模型、检索器、数据库还是权限服务。
- `operation_id` 用于查询写操作真实状态。

不要把 SQL、密钥、内部堆栈或其他租户数据直接放进最终答案。State 中的技术错误也应在输出边界做脱敏。

### 4.3 异常和错误状态何时使用

```text
代码 bug、状态契约被破坏、依赖初始化失败 -> 抛异常并报警
预期内业务分支，如无权限、无数据、预算耗尽 -> 结构化错误状态
可恢复技术故障 -> 由重试策略处理，最终失败再写入状态或抛出
```

如果所有错误都转成 State，严重代码 bug 可能被误当成普通业务结果；如果所有错误都抛异常，图就无法根据失败类型执行 fallback 或人工介入。两者需要分层。

## 5. Retry 和 Replan 不是一回事

```text
Retry：同一个节点、同一个目标，因临时失败再次执行
Replan：根据新信息改变后续步骤或任务拆分
```

网络超时可以 Retry；检索结果为空时通常需要改写 query 或改变检索器，这是 Replan。写操作发生 unknown 时，优先查询业务状态，不能把执行节点简单 Retry。

### 5.1 四种策略的关键区别

| 策略 | 是否改变输入或计划 | 适用场景 | 例子 |
|---|---|---|---|
| Retry | 通常不改变业务目标，可能仅退避等待 | 临时性、可恢复故障 | 模型接口返回 429，等待后重试 |
| Replan | 改变查询、工具或后续步骤 | 原计划无法达成目标 | 向量检索为空，改写 query 后重检 |
| Fallback | 切换备用能力或降级结果 | 主依赖不可用但可接受降级 | 主模型失败，切备用模型 |
| Human review | 暂停并等待人做决定 | 高风险、歧义或预算超限 | 发布报表前由负责人确认 |

Retry 不能修复确定性的参数错误。相同非法月份重试十次仍然非法；这类错误需要重新构造参数或询问用户。

### 5.2 退避和抖动

可重试的网络错误通常不要立即高频重试。常见策略是指数退避并加入随机抖动：

```text
第 1 次失败 -> 等待约 1 秒
第 2 次失败 -> 等待约 2 秒
第 3 次失败 -> 等待约 4 秒
```

随机抖动用于避免大量并发任务同时再次请求上游。重试次数和总时长都要有上限，并记录每次失败原因。

### 5.3 写操作的 unknown 状态

假设 Agent 调用“发布月报”接口：服务端已经发布成功，但响应在网络中丢失。客户端看到超时，不能直接再次发布，否则可能产生两份月报。

正确流程是：

```text
publish(report, idempotency_key)
 -> TIMEOUT / UNKNOWN
 -> query_publish_status(idempotency_key)
    | published -> 记录成功
    | not_found -> 再决定是否重试
    | still_unknown -> 人工介入
```

这就是为什么“错误是否可重试”不仅取决于错误码，还取决于操作是读还是写、下游是否支持幂等。

## 6. 并行节点和 reducer 冲突

多个独立子任务可以并行，但要明确：

- 是否会写同一个字段
- 是否有 reducer
- 结果是否需要稳定排序
- 一个分支失败是否取消全部分支
- 外部副作用是否幂等

“并行更快”不代表结果更稳定。对多个 BI 维度分析可以并行读数据，但最终合并要去重、标记来源和处理部分失败。

### 6.1 什么任务可以并行

只有在分支之间没有先后依赖时才适合并行。例如分析销售额下降原因：

```text
                    -> 按地区分析 -\
query_base_data     -> 按品类分析 --> merge
                    -> 按渠道分析 -/
```

三个维度都只读取基础数据，不依赖彼此结果，可以并行。若品类分析必须先知道下降最严重的地区，就不能直接并行。

并行前要核对外部服务并发限制。把十个模型节点并发执行可能更快，也可能同时触发限流，使整体失败率和费用上升。

### 6.2 同一 super-step 的状态更新

并行分支可能在同一执行阶段分别返回更新。若它们同时更新普通字段，运行时无法安全判断哪个值应该保留，通常会产生冲突。共享追加字段需要显式 reducer：

```python
import operator
from typing import Annotated, TypedDict


class AnalysisState(TypedDict, total=False):
    findings: Annotated[list[dict], operator.add]
```

每个节点返回自己的列表片段：

```python
return {"findings": [{"dimension": "region", "result": "华东下降"}]}
```

不要让每个分支读取旧列表、原地 append 后再返回整份列表。这会混淆增量语义，并在并行时造成重复或覆盖。

### 6.3 稳定排序和来源标记

并行完成顺序可能随网络延迟变化，所以最终报告不能依赖列表自然顺序。结果应包含：

```text
dimension：分析维度
source：数据来源或工具
status：success / no_data / failed
result：结构化发现
```

merge 节点按固定规则排序、去重并统计部分失败。这样同样输入即使分支完成顺序不同，最终报告仍稳定。

### 6.4 部分失败策略

并行分支中一个失败后，有三种策略：

```text
fail-fast：任何关键分支失败，整体停止
best-effort：保留成功分支，报告缺失维度
quorum：达到最低成功数量后继续
```

BI 分析通常适合 best-effort，但报告必须明确写出“渠道维度查询失败”，不能让模型把缺失维度解释成“渠道没有影响”。权限校验等关键分支则应 fail-fast。

## 7. 子图边界

适合提取子图的条件：

```text
有独立 State 或明确输入输出
内部流程可单独测试
被多个上层流程复用
有独立错误和恢复策略
```

子图边界不是文件拆分边界。过度拆分会让状态映射、调试和通信成本上升。

### 7.1 子图需要明确输入输出映射

假设主图 State 包含用户问题、权限、查询结果和报告，而“检索指标口径”子图只需要：

```text
输入：metric_name, tenant_id
输出：metric_definition, evidence, retrieval_status
```

子图不应该直接读取主图所有字段。输入越窄，越容易复用和测试，也越不容易意外接触敏感数据。

### 7.2 什么时候不应该拆子图

- 只有一个很短的节点，且没有独立控制流。
- 与主图共享大量字段，映射成本高于收益。
- 错误和恢复必须与主图统一处理。
- 只是为了把文件变短，没有真正的业务边界。

子图的价值在于封装一段完整能力，而不是制造更多层级。

### 7.3 Checkpoint 与恢复边界

配置 checkpointer 后，运行时可以在步骤边界保存状态，用 `thread_id` 等配置标识一条执行线程。恢复依赖的不只是“记住聊天记录”，还包括当前 State 和下一步执行位置。

需要特别注意：

- `thread_id` 必须由可信后端绑定当前用户和租户，不能直接相信客户端随意传入。
- checkpoint 中可能包含敏感数据，需要访问控制、加密和保留期限。
- 恢复后节点可能再次执行，外部写操作仍要幂等。
- 更新图结构或 State Schema 后，旧 checkpoint 可能不再兼容，需要版本迁移策略。

## 8. 把 Tool、Agent 和人工确认放进 Graph

Graph 的节点不一定是普通业务函数，也可以包装工具调用或一个完整 Agent：

```text
Graph：控制全局阶段、预算、权限、审核和终止
Agent Node：在一个受限阶段内自主选择只读工具
Tool Node：执行具体外部操作并返回结构化结果
```

例如“分析下降原因”可以是一个 Agent 节点，让模型在已授权的只读查询工具中选择；“发布报告”则由确定性节点执行，并在前面增加人工确认。

### 8.1 全局 Graph 与局部 Agent

```text
validate -> plan -> analysis_agent -> quality_check -> human_review -> publish
```

`analysis_agent` 可以 ReAct 循环，但它的工具集合、最大步数和输入数据由外层 Graph 限制。这样既保留模型探索能力，又不让它控制整个高风险流程。

### 8.2 Human-in-the-loop 的本质

人工介入不是简单地打印“请确认”，而是：

```text
1. 在确定的步骤暂停执行
2. 持久化当前状态和待确认操作
3. 向有权限的人展示足够的决策信息
4. 收到批准、拒绝或修改后恢复
5. 恢复时重新校验权限和数据时效
```

高风险操作应默认拒绝。不能因为 checkpoint 中有 `approved=True` 就永远相信它，还应绑定审批人、操作摘要、有效期和请求版本，防止审批后参数被替换。

## 9. BI Agent 的完整流程设计

一个生产级“为什么本月销售额下降”流程可以设计为：

```text
validate_request
 -> plan
 -> retrieve_metric_definition
 -> query_realtime_data
 -> fan_out_dimensions
      | region_analysis
      | category_analysis
      | channel_analysis
 -> merge_findings
 -> quality_check
      | pass -> generate_report -> END
      | insufficient + budget_available -> replan -> query_realtime_data
      | conflicting -> human_review
      | budget_exceeded -> partial_report -> END
```

### 9.1 每一层的责任

| 节点 | 主要输入 | 主要输出 | 失败策略 |
|---|---|---|---|
| `validate_request` | 用户、租户、月份、指标 | 授权范围、规范参数 | 参数错误或无权限立即结束 |
| `plan` | 规范问题、预算 | 查询与分析计划 | 计划不可解析则有限重试 |
| `retrieve_metric_definition` | 指标名 | 口径、计算规则、来源 | 请求澄清或标记无口径 |
| `query_realtime_data` | 授权条件、SQL DSL | 结构化数据、查询 ID | 超时有限重试，权限错误停止 |
| 各维度分析 | 基础数据 | 带来源的 findings | best-effort 或关键分支失败 |
| `quality_check` | 证据、findings | pass/replan/review | 由代码预算限制 replan |
| `generate_report` | 已验证证据 | 报告和引用 | 不允许创造 State 中不存在的数值 |

### 9.2 RAG 和实时查询不要混为一谈

```text
RAG：查指标定义、业务规则、历史报告等非实时知识
数据工具：查本月销售额、地区明细等实时或权限敏感数据
```

向量库中的历史报告不能替代实时数据库结果；模型也不能根据检索到的旧数值回答本月数据。State 应分别保存 `metric_evidence` 和 `query_results`，报告中的每个数字应能追溯到查询 ID。

### 9.3 质量检查检查什么

质量检查不应只问模型“答案好不好”，至少要有确定性规则：

- 报告中的数值是否能在查询结果中找到。
- 环比下降的计算方向和分母是否正确。
- 是否覆盖用户有权查看且计划要求的维度。
- 部分失败是否被明确披露。
- 指标口径和时间范围是否一致。
- 是否超过 replan、token 和查询预算。

模型可以补充语义质量判断，但不能替代数值一致性校验。

## 10. practice/09 的阅读方法

对应代码：[practice/Agent开发实战/09-langgraph-workflow](../../practice/Agent开发实战/09-langgraph-workflow/README.md)

按 `classify -> retrieve -> after_retrieve -> rewrite` 阅读，而不是先看所有节点。重点观察：

1. `route` 由代码明确决定。
2. `attempts` 是防循环的状态字段。
3. `rewrite` 只改变 query，不直接检索。
4. `answer` 对空 context 返回明确的 unknown。

### 10.1 direct 路径

输入：

```python
{"question": "你好", "attempts": 0}
```

执行过程：

```text
classify 返回 {route: direct}
 -> 条件边映射 direct 到 answer
 -> answer 不读取知识库，生成直接回答
 -> END
```

最终 `attempts` 仍为 0，这不仅验证答案文本，还证明 `retrieve` 确实没有执行。测试跳过路径时，应优先断言“不该产生的副作用或状态没有出现”。

### 10.2 knowledge 且检索成功路径

```text
question 包含 Runnable
 -> classify: route=knowledge
 -> retrieve: context=定义, attempts=1
 -> after_retrieve: context 非空，返回 answer
 -> answer: 使用 context
 -> END
```

注意条件函数看到的是 `retrieve` 更新合并后的 State，因此它能读到最新的 `context` 和 `attempts=1`。

### 10.3 knowledge 但检索为空路径

当问题包含 `Tool` 或 `LangChain` 时会进入 knowledge 路径，但当前假检索器只认识 `Runnable`：

```text
retrieve 第一次：context="", attempts=1
 -> after_retrieve 返回 rewrite
 -> rewrite 修改 question
 -> retrieve 第二次：context="", attempts=2
 -> after_retrieve 返回 answer
 -> answer 返回“知识库没有找到答案”
```

这个路径证明循环可以结束，但也暴露一个设计简化：`rewrite` 只是加前缀，并没有判断新 query 是否与旧 query 语义重复。生产实现应记录 `seen_queries`，避免无效改写。

### 10.4 当前练习的边界

练习主要用于理解路由和循环，尚未实现：

- 真实向量检索和相关性评分。
- 结构化错误码与超时重试。
- checkpoint、暂停和恢复。
- token、时间和工具调用总预算。
- 非法 route 的 fallback。
- 并行节点与 reducer。

学习时不要把示例的简洁实现误认为生产方案。先理解最小机制，再按风险逐层增加保护。

## 11. 测试复杂 Graph 的方法

### 11.1 路由覆盖测试

每一个条件边标签都至少需要一条测试。对练习应覆盖：

```text
classify -> direct
classify -> knowledge
after_retrieve -> answer
after_retrieve -> rewrite
```

还应测试路由函数返回非法值时明确失败，避免未来修改分类逻辑后悄悄走错路径。

### 11.2 循环边界测试

不要只测“一次成功”，还应注入永远返回空结果的检索器，并断言：

```text
retrieve 恰好调用上限次数
最终 status/answer 表示证据不足
没有再发起额外模型或工具调用
```

对超时预算可使用假时钟，避免测试真的等待。对 token 和工具次数可注入计数器。

### 11.3 失败和副作用测试

重点测试这些不变量：

- `FORBIDDEN` 后查询函数调用次数为 0。
- 读操作 `TIMEOUT` 在上限内重试。
- 写操作 `UNKNOWN` 进入状态查询而不是再次写入。
- 并行分支部分失败时，成功结果保留且报告标记缺失。
- 人工拒绝后发布函数调用次数为 0。

对 Agent 系统而言，“危险动作没有发生”通常比“最终字符串包含某句话”更重要。

### 11.4 重放和确定性

路由、reducer、参数校验等纯逻辑应在相同 State 下得到相同结果。模型调用和实时数据查询不是确定性的，因此要记录模型版本、Prompt 版本、工具参数、查询 ID 和关键输出，才能复盘一次执行。

重放不等于重新调用所有外部工具。对有副作用的历史步骤，应读取已保存结果或查询业务状态。

## 12. 可执行实验

1. 把 `MAX_ATTEMPTS` 思路改成 1，确认循环最多执行一次。
2. 让 `retrieve` 永远返回空 context，观察是否终止。
3. 让 `route` 返回未知标签，补一个测试保证错误暴露。
4. 增加 `error_code="TIMEOUT"` 分支，允许有限重试；增加 `FORBIDDEN` 分支，验证不会重试。

继续完成以下实验：

5. 为“Tool 是什么”补测试，断言 `attempts == 2` 且最终返回知识库无结果。
6. 给 State 增加 `seen_questions`，如果改写结果重复则提前结束。
7. 把最大尝试次数提取成可信配置，但不要放进模型可修改的 State 字段。
8. 将检索器作为 `build_graph(retriever)` 的依赖注入，测试成功、空结果和抛异常。
9. 增加 `status` 和 `error_code`，确保成功、无结果和系统异常能够区分。
10. 使用 `stream_mode="updates"` 打印空结果路径，手工画出每轮 State 变化。

## 13. 常见设计错误

### 13.1 用自然语言决定所有路由

“请判断下一步做什么”返回自由文本，既难解析又难测试。应使用结构化输出映射到有限标签，并由程序处理未知值。

### 13.2 只设置最大循环次数

次数上限防止死循环，但不能控制一次调用卡住十分钟或单次消耗大量 token。还要设置节点超时和总预算。

### 13.3 所有失败都 Retry

权限错误、参数错误、预算耗尽和写操作 unknown 都不应原样重试。Retry 策略必须同时考虑错误类型和操作语义。

### 13.4 把敏感权限写进 Prompt

Prompt 中说“只能看华东”不是权限控制。真正的查询接口必须根据可信 `user_id/tenant_id` 再次校验，且这些身份不能由模型参数覆盖。

### 13.5 并行结果直接拼接

没有来源、状态和稳定排序的结果会因执行顺序产生不同报告，也无法区分无数据与查询失败。先结构化合并，再生成自然语言。

## 14. 自测

1. 为什么条件边只返回标签？
2. 程序如何保证循环不会被模型无限延长？
3. Retry 和 Replan 的判断依据是什么？
4. 写操作返回 unknown 时为什么不能直接重试？
5. 多个并行节点同时更新一个字段时需要什么？
6. 为什么 `Literal` 不能防止模型在运行时返回非法 route？
7. 业务终止条件和运行时递归限制分别解决什么问题？
8. `TIMEOUT` 为什么不能单独决定是否重试？
9. 并行分析中 best-effort 的结果应该如何向最终报告披露？
10. 子图边界为什么不等于文件边界？
11. checkpoint 恢复后为什么仍要考虑节点幂等？
12. BI Agent 中为什么指标口径 RAG 与实时数据查询要分开？
13. Human-in-the-loop 恢复执行时为什么需要重新校验审批和权限？
14. Graph + Agent Node 相比让单个 Agent 控制全流程有什么优势？

## 官方资料

- [Conditional edges](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph workflows](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
