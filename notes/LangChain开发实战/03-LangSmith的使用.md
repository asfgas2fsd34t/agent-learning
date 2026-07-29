# 03 LangSmith 的使用

> 来源：`尚硅谷-03-LangSmith的使用.pdf`。

## 学习目标

- 理解 LangSmith 在 LLM 应用中的作用
- 为模型、Chain、Tool 和 Agent 开启 Trace
- 看懂一次运行的输入、输出、耗时、Token 和错误
- 理解 Dataset、Experiment、Evaluator 和人工标注的关系
- 明确生产日志中的隐私和权限边界

## 1. 什么是 LangSmith

LangSmith 是面向 LLM 应用的开发和运维平台，主要能力可以分为四组。

### 1.1 可观测性

- **Tracing**：记录一次请求经过的模型、Runnable、Retriever 和 Tool
- **Monitoring**：观察线上错误率、延迟、Token 和反馈
- **Annotation Queues**：把问题样本分配给人工标注

### 1.2 评估

- **Datasets**：保存版本化测试样本
- **Experiments**：在固定数据集上运行候选版本
- **Evaluators**：使用规则、代码、模型或人工评分

### 1.3 提示词与调试

- Prompt 管理和版本对比
- Playground 中快速试验模型和参数
- Studio 中观察 LangGraph 应用

### 1.4 部署相关能力

LangSmith 生态还提供部署和运行相关能力，但是否采用应根据团队基础设施决定。使用 LangChain 并不强制使用 LangSmith。

## 2. 为什么 Agent 更需要 Trace

普通模型调用只有一层：

```text
输入 -> 模型 -> 输出
```

Agent 可能包含多轮模型和工具调用：

```text
用户问题
-> 模型判断
-> Tool A
-> 模型再次判断
-> Tool B
-> 最终回答
```

只记录最终答案无法定位：

- 模型为什么选择某个工具
- 工具参数是否正确
- 哪一步出现超时或异常
- 哪次模型调用消耗最多 Token
- 中间件是否生效
- 最终回答引用了哪个工具结果

LangSmith Trace 用树状运行记录把这些步骤关联起来。

## 3. 开启 Tracing

常见环境变量：

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-key>
LANGSMITH_PROJECT=agent-learning
```

如果使用自定义区域或地址，再根据平台配置 Endpoint。API Key 不能提交到 Git。

```python
from dotenv import load_dotenv

load_dotenv(override=True)
```

启用后，支持 LangSmith 的 LangChain 调用会自动上报 Trace，业务代码通常不需要手动包裹每个模型调用。

## 4. 一条 Trace 包含什么

一次运行通常包含：

```text
Run 名称和类型
输入与输出
父子调用关系
开始时间和结束时间
总耗时
模型和参数
Token 用量
错误与堆栈
Tags 和 Metadata
用户反馈或评估分数
```

Agent Trace 中常见层级：

```text
Agent Run
├── Model Run
├── Tool Run
├── Model Run
└── Final Output
```

## 5. 使用 Runnable Config 增强追踪

```python
config = {
    "run_name": "sales_agent",
    "tags": ["agent", "learning"],
    "metadata": {
        "feature": "sales-analysis",
        "version": "v1",
    },
}

result = agent.invoke(
    {"messages": [{"role": "user", "content": "分析本月销售"}]},
    config=config,
)
```

设计建议：

- `run_name` 使用稳定、可理解的业务名称
- `tags` 用于环境、模块和实验版本分类
- `metadata` 只记录必要且脱敏的信息
- 用业务请求 ID 关联应用日志和 Trace

## 6. 监控指标

### 6.1 可靠性

- 请求成功率
- 模型错误率
- Tool 错误率
- 重试率
- 超时率

### 6.2 性能

- 总延迟
- 首 Token 延迟
- 模型耗时
- Tool 耗时
- P50、P95、P99 延迟

### 6.3 成本

- 输入 Token
- 输出 Token
- 单请求成本
- 按模型、租户或功能聚合的成本

### 6.4 Agent 行为

- 模型调用次数
- Tool 调用次数
- 最大执行步数
- 人工介入率
- 终止原因

平均值可能掩盖少量严重错误，需要同时观察分位数和失败样本。

## 7. Dataset 与 Experiment

### 7.1 Dataset

Dataset 是可重复使用的测试样本集合，一条样本通常包含：

```json
{
  "inputs": {
    "question": "普通订单退款需要多久？"
  },
  "outputs": {
    "required_points": ["3-5 个工作日"]
  }
}
```

数据来源可以是：

- 已脱敏的真实问题
- 历史故障样本
- 典型和边界问题
- 无答案和安全问题

### 7.2 Experiment

Experiment 在同一 Dataset 上运行一个确定版本：

```text
数据集 v1
-> Prompt A + Model A
-> 得到实验结果 A

数据集 v1
-> Prompt B + Model A
-> 得到实验结果 B
```

只有固定数据集、模型、参数和知识版本，比较结果才有解释性。

## 8. Evaluator

评估器可以分为：

### 8.1 确定性评估

- JSON 能否解析
- 字段和枚举是否合法
- 是否包含要求内容
- 是否调用了禁止工具
- 延迟和 Token 是否超限

确定性规则稳定、便宜，应优先使用。

### 8.2 LLM-as-a-Judge

让模型根据 Rubric 评价事实、完整性、相关性和表达。它适合开放式回答，但评审模型也会产生偏差，必须固定模型、Prompt 和参数，并通过人工样本校准。

### 8.3 人工评估

人工适合判断复杂事实、业务可用性和高风险结果。Annotation Queue 可以把待审样本分配给领域人员。

生产评估通常组合：

```text
代码规则 + 模型评审 + 人工抽样 + 业务指标
```

## 9. 从 Trace 到优化闭环

```text
线上发现异常
-> 打开对应 Trace
-> 确认失败发生在模型、工具还是流程
-> 把样本加入 Dataset
-> 修改一个主要变量
-> 运行 Experiment
-> 自动评估和人工抽查
-> 灰度发布
-> 继续监控
```

Trace 用于定位问题，Dataset 用于固定问题，Experiment 用于比较版本，Evaluator 用于判断是否改善。

## 10. 数据安全

Trace 可能包含：

- 用户输入
- System Prompt
- 检索文档
- Tool 参数和结果
- 业务 Metadata

生产接入前必须明确：

- 哪些字段允许上报
- 敏感信息如何脱敏
- 不同环境和租户如何隔离
- 谁可以查看和导出 Trace
- 数据保留和删除期限
- 第三方服务是否满足合规要求

不能为了调试方便而默认上传完整客户数据、凭证或内部机密。

## 总结

```text
Tracing：看一次请求发生了什么
Monitoring：看线上整体是否健康
Dataset：保存可复现测试样本
Experiment：比较不同版本
Evaluator：判断结果质量
Annotation Queue：组织人工评审
```

LangSmith 不是 Agent 的业务数据库，也不能替代应用日志、权限审计和业务监控。它的核心价值是让 LLM 应用的执行过程可观察、可比较、可回归。
