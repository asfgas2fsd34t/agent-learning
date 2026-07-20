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

## 深入：`create_agent()` 不是一个黑盒函数

`create_agent()` 返回的是一个编译后的图结构。虽然调用方式看起来简单：

```python
agent = create_agent(model=model, tools=[query_sales])
```

内部至少包含这些角色：

```text
模型节点：决定直接回答还是调用工具
工具节点：根据 tool_calls 找到并执行工具
状态：保存 messages 和结构化响应
边：根据模型是否产生 tool_calls 决定继续还是结束
```

可以把默认循环理解为：

```text
START
-> model
-> 有 tool_calls：tools
-> tool 结果回到 model
-> 没有 tool_calls：END
```

`create_agent()` 负责把上一课手动维护的消息协议和循环控制封装起来，但不会替你解决业务权限、数据真实性和危险操作审批。

## `bind_tools()` 与 `create_agent()` 的边界

| 能力 | `bind_tools()` | `create_agent()` |
|---|---|---|
| 给模型提供工具 Schema | 是 | 是 |
| 执行工具 | 否 | 是 |
| 自动把 ToolMessage 返回模型 | 否 | 是 |
| 多轮工具循环 | 否 | 是 |
| 保存 Agent State | 通常由调用方维护 | 是 |
| 权限和业务校验 | 否 | 仍需业务代码 |
| 人工审批和持久化 | 需要自行编排 | 通过 middleware/checkpointer 配置 |

选择原则：

```text
只想控制一次模型请求和消息协议 -> bind_tools
需要工具执行和循环 -> create_agent
需要复杂分支、并行、审批和恢复 -> LangGraph 显式工作流
```

## Agent 状态如何推进

一次 `invoke` 不只是返回答案，还会产生状态变化：

```text
初始：messages = [HumanMessage]
模型后：追加 AIMessage(tool_calls)
工具后：追加 ToolMessage
最终模型后：追加 AIMessage(content)
```

因此调试 Agent 时不要只打印最后一句话，应检查完整消息历史：

```python
result = agent.invoke({"messages": [...]})

for index, message in enumerate(result["messages"]):
    print(index, type(message).__name__, message.content)
    if getattr(message, "tool_calls", None):
        print("tool_calls:", message.tool_calls)
```

很多“Agent 答错”其实发生在最终回答之前：工具选错、参数错、工具返回空数据或错误消息没有正确回传。

## Agent 的终止不是只有“模型回答了”

至少要区分：

```text
正常结束：模型没有继续提出工具调用
步数结束：达到最大模型或工具调用次数
错误结束：不可重试错误、权限失败或参数无法修正
人工暂停：等待审批、补充信息或接管
超时结束：超过总任务时间
```

生产系统必须把这些状态区分开，否则用户只能看到模糊的“Agent 失败”。

## 工具循环中的错误传播

```text
工具抛出异常
-> ToolNode/Middleware 转换错误
-> ToolMessage 返回模型
-> 模型决定修正、重试、换工具或结束
```

但不是所有错误都应该返回模型后重试：

| 错误 | 推荐行为 |
|---|---|
| 网络超时 | 有限重试 |
| 参数格式错误 | 修正参数 |
| 无权限 | 立即结束，不允许绕过 |
| 无数据 | 明确告诉用户 |
| 业务状态不允许 | 结束或人工处理 |
| 结果质量不足 | Reflection 或补充查询 |

## 深入实验

### 实验一：观察完整状态

分别提问：

```text
查询 2026-06 华东销售额
查询 2026-06 华南销售额
```

打印每一条 message，区分模型请求、工具结果和最终回答。

### 实验二：让工具返回错误

查询一个不存在的月份，观察：

```text
工具返回 NO_DATA
-> 模型是继续查询、直接回答还是编造结果？
```

然后修改 System Prompt 和工具错误结构，比较行为变化。

### 实验三：设置循环上限

加入 `ModelCallLimitMiddleware` 或 `ToolCallLimitMiddleware`，制造重复查询，观察 Agent 如何结束以及最终状态如何表示。

## 对应实践

[practice/Agent开发实战/04-langchain-agent](../../practice/Agent开发实战/04-langchain-agent/README.md) 构建销售分析 Agent，让模型根据问题自主选择销售查询工具并完成最终回答。

## 自测

1. `create_agent()` 与 `bind_tools()` 有什么区别？
2. Agent 为什么可能调用多个工具？
3. 哪些规则必须写在业务代码中？
4. Agent 在什么条件下结束？

## 官方资料

- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [create_agent API](https://reference.langchain.com/python/langchain/agents/factory/create_agent)
