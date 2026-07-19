# 07 Agent 安全与中间件

## 学习目标

使用 LangChain v1 middleware 在模型调用和工具调用周围增加横切控制，同时明确 middleware 不能替代业务服务。

## 中间件位置

```text
before_model -> 模型调用 -> after_model
                         |
                 wrap_tool_call
```

常见用途：

- 模型调用次数限制
- 工具调用次数限制
- 动态 System Prompt
- PII 检测与脱敏
- 工具异常转换
- 危险工具人工确认
- 日志和 Trace

## 内置 middleware

LangChain v1 提供 `ModelCallLimitMiddleware`、`ToolCallLimitMiddleware`、`HumanInTheLoopMiddleware`、`SummarizationMiddleware` 等组件。

```python
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[
        ModelCallLimitMiddleware(run_limit=5),
        ToolCallLimitMiddleware(tool_name="query_sales", run_limit=3),
    ],
)
```

## 人工确认

危险写操作应在执行工具之前暂停：

```python
HumanInTheLoopMiddleware(
    interrupt_on={"refund_order": True}
)
```

这要求 Agent 配置 Checkpointer，审批结果由应用端用户提交，不能让模型自己批准。

## 权限与幂等

Middleware 可以拒绝明显不合规的调用，但最终权限必须在业务服务根据登录用户校验。幂等键应由应用或业务服务生成并复用，不能依赖模型每次生成相同字符串。

## 错误与重试

```text
参数错误：通常不可重试，返回明确字段错误
限流/临时网络错误：有限重试
结果 unknown：查询业务状态，不重复发起写操作
权限失败：不可重试
```

## 对应实践

[practice/11-agent-middleware](../../practice/11-agent-middleware/README.md) 使用模型调用限制、工具调用限制和业务权限函数，演示 middleware 与业务服务的分工。

## 自测

1. Middleware 与业务服务权限校验有什么区别？
2. 为什么人工确认不能由模型完成？
3. 写操作超时后为什么要先查询状态？
4. 什么错误适合自动重试？

## 官方资料

- [Middleware](https://docs.langchain.com/oss/python/langchain/middleware)
- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)

