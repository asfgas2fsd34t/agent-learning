# 12 LangGraph 基础

## 学习目标

理解 `State`、`Node`、`Edge`、`START/END` 和编译执行。LangGraph 不是另一种 Prompt，而是显式描述状态如何经过多个步骤变化。

## 核心结构

```python
from typing import TypedDict
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    topic: str
    outline: list[str]
    draft: str


builder = StateGraph(State)
builder.add_node("plan", plan_node)
builder.add_node("write", write_node)
builder.add_edge(START, "plan")
builder.add_edge("plan", "write")
builder.add_edge("write", END)
graph = builder.compile()
```

## State

State 是节点之间共享的数据协议。节点接收当前 State，返回需要更新的字段：

```python
def plan_node(state: State) -> dict:
    return {"outline": ["定义", "原理", "边界"]}
```

不要返回与 State 无关的任意数据。字段含义稳定，图才容易调试和恢复。

## Node

Node 是一个可执行步骤，可以是普通函数、Runnable 或异步函数。节点应职责单一，并把外部副作用隔离到明确服务中。

## Edge

Edge 决定执行顺序。普通 Edge 是固定路径，条件 Edge 根据 State 选择下一节点。

## compile 与 invoke

Builder 只是在描述图，`compile()` 才生成可执行图。编译后的图支持 `invoke/ainvoke/stream`，本身也符合 Runnable 接口。

## 对应实践

[practice/16-langgraph-basics](../../practice/16-langgraph-basics/README.md) 实现“规划提纲 -> 生成草稿”的单 Agent 图。

## 自测

1. State 为什么是图的公共协议？
2. Node 应返回完整 State 还是增量字段？
3. `compile()` 前后对象有什么区别？
4. LangGraph 与一条线性 LCEL Chain 的区别是什么？

## 官方资料

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

