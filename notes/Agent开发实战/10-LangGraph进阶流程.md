# 13 LangGraph 进阶流程

## 1. 先把控制流写成状态机

复杂 Agent 流程不是“加一个更强的 Prompt”就能稳定。先定义状态和合法路径：

```text
classify -> direct_answer -> END
        \-> retrieve -> evaluate
                         | enough -> answer -> END
                         | retry  -> rewrite -> retrieve
```

每条路径都应回答：输入是什么、输出更新什么、失败去哪、何时结束、是否可以重试。

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

## 4. 错误状态要进入 State

不要让所有异常都表现成同一个 `Exception`。可以在 State 中建模：

```text
status: running | completed | unknown | forbidden | failed
error_code: INVALID_ARGUMENT | TIMEOUT | FORBIDDEN | UPSTREAM_ERROR
attempts: int
```

路由依据 `error_code` 决定是否重试。参数错误应返回用户修正；权限错误应停止；临时上游错误可在上限内重试；结果 unknown 需要查询状态或人工介入。

## 5. Retry 和 Replan 不是一回事

```text
Retry：同一个节点、同一个目标，因临时失败再次执行
Replan：根据新信息改变后续步骤或任务拆分
```

网络超时可以 Retry；检索结果为空时通常需要改写 query 或改变检索器，这是 Replan。写操作发生 unknown 时，优先查询业务状态，不能把执行节点简单 Retry。

## 6. 并行节点和 reducer 冲突

多个独立子任务可以并行，但要明确：

- 是否会写同一个字段
- 是否有 reducer
- 结果是否需要稳定排序
- 一个分支失败是否取消全部分支
- 外部副作用是否幂等

“并行更快”不代表结果更稳定。对多个 BI 维度分析可以并行读数据，但最终合并要去重、标记来源和处理部分失败。

## 7. 子图边界

适合提取子图的条件：

```text
有独立 State 或明确输入输出
内部流程可单独测试
被多个上层流程复用
有独立错误和恢复策略
```

子图边界不是文件拆分边界。过度拆分会让状态映射、调试和通信成本上升。

## 8. practice/09 的阅读方法

对应代码：[practice/Agent开发实战/09-langgraph-workflow](../../practice/Agent开发实战/09-langgraph-workflow/README.md)

按 `classify -> retrieve -> after_retrieve -> rewrite` 阅读，而不是先看所有节点。重点观察：

1. `route` 由代码明确决定。
2. `attempts` 是防循环的状态字段。
3. `rewrite` 只改变 query，不直接检索。
4. `answer` 对空 context 返回明确的 unknown。

## 9. 可执行实验

1. 把 `MAX_ATTEMPTS` 思路改成 1，确认循环最多执行一次。
2. 让 `retrieve` 永远返回空 context，观察是否终止。
3. 让 `route` 返回未知标签，补一个测试保证错误暴露。
4. 增加 `error_code="TIMEOUT"` 分支，允许有限重试；增加 `FORBIDDEN` 分支，验证不会重试。

## 10. 自测

1. 为什么条件边只返回标签？
2. 程序如何保证循环不会被模型无限延长？
3. Retry 和 Replan 的判断依据是什么？
4. 写操作返回 unknown 时为什么不能直接重试？
5. 多个并行节点同时更新一个字段时需要什么？

## 官方资料

- [Conditional edges](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph workflows](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
