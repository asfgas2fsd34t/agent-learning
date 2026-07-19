# 05 上下文与 Memory

## 学习目标

让 Agent 在同一个会话中记住前文，同时保证不同会话隔离，并理解 Checkpointer 与上下文窗口不是同一个概念。

## 两个关键概念

```text
Checkpointer：保存 Agent 每一步状态
上下文窗口：模型一次请求最多能处理的 token
```

保存了状态不代表所有历史都应该无限传给模型。历史过长仍需裁剪或摘要。

## 使用 Checkpointer

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=InMemorySaver(),
)
```

每个会话使用稳定的 `thread_id`：

```python
config = {"configurable": {"thread_id": "conversation_1001"}}
agent.invoke({"messages": [...]}, config=config)
```

相同 `thread_id` 继续同一会话，不同 `thread_id` 必须隔离。

## 短期与长期记忆

短期记忆保存当前任务消息、工具结果和执行状态。长期记忆保存跨会话仍有价值的用户偏好或稳定事实。长期记忆不能每次全量注入，应按当前问题召回。

## 上下文治理

- 只保留与当前任务有关的消息。
- 工具返回只保留必要字段，避免塞入完整数据库结果。
- 长对话使用摘要，但保留关键决策、约束和未完成状态。
- 敏感信息不应因为“记忆”而永久保存。
- 用户明确说“本次”时，不应覆盖长期偏好。

## 持久化选择

`InMemorySaver` 适合学习和单进程测试，服务重启后状态丢失。生产环境应使用官方支持的数据库 Checkpointer，并设置租户隔离、保留期限和加密策略。

## 对应实践

[practice/09-langchain-memory](../../practice/09-langchain-memory/README.md) 使用 `thread_id` 维护两个隔离会话，并验证同一会话能够回答上一轮提供的信息。

## 自测

1. Checkpointer 和上下文窗口有什么区别？
2. 为什么不能无限保存所有消息？
3. `thread_id` 为什么不能由模型决定？
4. `InMemorySaver` 为什么不适合多实例生产部署？

## 官方资料

- [Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

