# 13 LangGraph 进阶流程

## 学习目标

使用条件边、循环、路由和失败状态表达可控工作流。

## 条件路由

```python
builder.add_conditional_edges(
    "classify",
    route_question,
    {"knowledge": "retrieve", "direct": "answer"},
)
```

路由函数只返回路径标签，不直接执行节点。

## 循环

检索质量不足时可以改写问题后再次检索：

```text
retrieve -> evaluate
             | enough -> answer
             | retry  -> rewrite -> retrieve
```

循环必须在 State 中记录 `attempts`，并有最大次数。不能只依赖 Prompt 要求“不要无限循环”。

## 错误分支

将失败分为：

```text
可重试临时错误
不可重试参数错误
权限失败
结果 unknown
```

不同错误进入不同节点。写操作 unknown 应查询业务状态，而不是回到执行节点重新写。

## 并行与 reducer

多个互不依赖的节点可以从同一节点并行出发。它们同时更新同一字段时，需要 reducer 规定合并规则，否则会发生状态冲突。

## 子图

当一段流程有独立 State、清晰输入输出并可单独测试时，可以提取子图。不要为了“看起来模块化”把每两个节点都拆成子图。

## 对应实践

[practice/17-langgraph-workflow](../../practice/17-langgraph-workflow/README.md) 实现问题路由、检索质量判断和最多两次的改写循环。

## 自测

1. 条件函数为什么只返回标签？
2. 如何从代码层保证循环有上限？
3. unknown 状态为什么不能直接重试写操作？
4. 什么情况下需要 reducer？

