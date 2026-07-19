# 04 LangChain Agent

## 学习目标

本课使用 LangChain v1 的 `create_agent()`，把上一课手动执行的一轮工具调用升级为完整循环。

## Agent 执行循环

```text
用户消息
-> 模型判断是否调用工具
-> 执行工具
-> ToolMessage 返回模型
-> 模型继续判断
-> 生成最终回答或再次调用工具
```

`create_agent()` 返回的是编译后的 LangGraph，而不是旧版 `AgentExecutor`：

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=[query_sales],
    system_prompt="需要真实数据时必须调用工具。",
)
```

调用：

```python
result = agent.invoke(
    {"messages": [{"role": "user", "content": "查询六月华东销售额"}]}
)
```

最终状态中的 `messages` 包含用户消息、模型工具请求、工具结果和最终回答。

## System Prompt 的职责

适合放：

- 角色和目标
- 工具选择规则
- 无数据时拒绝编造
- 输出风格和格式

不适合只靠 Prompt 实现：

- 权限
- 幂等
- 金额限制
- 数据范围隔离
- 危险操作审批

## Agent 的终止

正常终止发生在模型不再请求工具并生成最终回答。生产环境还需要模型调用上限、工具调用上限、超时和不可重试错误，避免无限循环。

## 结构化响应

`create_agent` 支持 `response_format`。适合业务端必须消费固定结构的场景，但结构校验通过仍不代表内容真实。

## 对应实践

[practice/08-langchain-agent](../../practice/08-langchain-agent/README.md) 构建销售分析 Agent，让模型根据问题自主选择销售查询工具并完成最终回答。

## 自测

1. `create_agent()` 与 `bind_tools()` 有什么区别？
2. Agent 为什么可能调用多个工具？
3. 哪些规则必须写在业务代码中？
4. Agent 在什么条件下结束？

## 官方资料

- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [create_agent API](https://reference.langchain.com/python/langchain/agents/factory/create_agent)

