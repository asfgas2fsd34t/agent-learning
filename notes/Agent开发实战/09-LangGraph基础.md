# 12 LangGraph 基础

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

## 3. Reducer：多个更新如何合并

普通字段通常是“后一次更新覆盖前一次”。如果并行节点都要追加结果，需要显式 reducer：

```python
import operator
from typing import Annotated, TypedDict


class ParallelState(TypedDict, total=False):
    findings: Annotated[list[str], operator.add]
```

没有 reducer 时，两个节点同时写 `findings` 可能发生冲突或丢数据。Reducer 只定义合并方式，不自动解决重复、顺序、事务和权限问题；这些仍要在节点或服务层处理。

## 4. Builder 到 Compiled Graph

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

## 5. Edge 的执行语义

- 普通 edge：节点成功后固定进入下一个节点。
- Conditional edge：调用路由函数，根据当前 State 选择目标。
- `END`：流程结束并返回最终 State。

路由函数只负责返回“去哪”，不要在路由函数里调用数据库或模型。这样路由可以被单元测试，副作用也不会因为路由重算而重复发生。

## 6. practice/08 的数据流

对应代码：[practice/Agent开发实战/08-langgraph-basics](../../practice/Agent开发实战/08-langgraph-basics/README.md)

```text
输入 {topic}
 -> plan_node 写入 outline
 -> write_node 读取 topic + outline，调用 writer
 -> 写入 draft
 -> END 返回完整 State
```

练习把 writer 作为函数注入，所以测试可以用假实现，不需要真实模型。这是一个值得保留的工程习惯：把模型调用和图结构分开，先测试控制流，再做集成测试。

## 7. 可执行实验

1. 在 `plan_node` 返回未知字段，观察编译或执行时的行为。
2. 让 `writer` 抛出异常，记录图在哪一步停止。
3. 给 State 增加 `status`，让每个节点只更新自己负责的状态。
4. 用 `graph.stream(..., stream_mode="updates")` 观察每个节点的增量更新。

## 8. LangGraph 与 LCEL 的取舍

```text
固定输入 -> 固定输出 -> 固定顺序：LCEL Chain
模型选择工具：Agent
多节点状态、循环、恢复和人工介入：LangGraph
```

LangGraph 不是所有函数的替代品。图越大，State 和边越难维护；只有在控制流或恢复语义确实需要显式建模时才引入它。

## 9. 自测

1. 为什么 Node 应返回增量字段而不是随意返回值？
2. 普通字段和带 reducer 的字段合并行为有什么区别？
3. `compile()` 和 `invoke()` 分别完成什么工作？
4. 为什么路由函数不应直接执行副作用？
5. 什么时候 Chain 比 Graph 更合适？

## 官方资料

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
