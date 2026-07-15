# Agent 核心概念笔记

## 学习目标

学完本节，需要能讲清楚：

- 什么是 AI Agent
- Agent 的核心能力有哪些
- 感知、推理、决策、执行分别是什么意思
- Agent 和普通 LLM 的区别
- Agent 常见应用场景有哪些

一句话版本：

**LLM 更像一个会生成答案的大脑，Agent 是把 LLM 放进一个能感知环境、做决策、调用工具、执行任务、根据结果继续调整的系统里。**

---

## 1. 什么是 AI Agent

AI Agent 可以理解为一个“能围绕目标自主完成任务的智能系统”。

它通常不只是回答一句话，而是会经历一个循环：

```text
接收目标 -> 理解环境 -> 推理分析 -> 做出决策 -> 调用工具或执行动作 -> 观察结果 -> 继续下一步
```

比如用户说：

```text
帮我分析这个项目为什么测试失败，并尝试修复。
```

普通 LLM 可能会：

- 根据你贴出来的报错给建议
- 解释可能原因
- 写一段修复代码

Agent 则可能会：

- 读取项目文件
- 运行测试
- 查看报错
- 定位相关代码
- 修改代码
- 再次运行测试
- 总结修复过程

所以 Agent 的重点不是“会说”，而是“能围绕目标行动”。

---

## 2. Agent 的核心能力

### 2.1 感知 Perception

感知是指 Agent 获取外部信息的能力。

对人来说，感知来自眼睛、耳朵、触觉。对软件 Agent 来说，感知来自：

- 用户输入
- 文件内容
- 数据库查询结果
- API 返回结果
- 命令行输出
- 网页内容
- 日志和报错
- 历史对话

例子：

```text
用户：这个接口为什么报 500？
Agent 感知到的信息：
- 用户的问题
- 接口代码
- 日志
- 请求参数
- 数据库状态
```

感知能力越好，Agent 越不容易凭空猜。

### 2.2 推理 Reasoning

推理是指 Agent 根据已有信息分析问题、形成判断的能力。

推理会回答这些问题：

- 当前任务目标是什么？
- 已知信息够不够？
- 可能原因有哪些？
- 下一步应该查什么？
- 哪个方案风险更小？

例子：

```text
日志显示 NullPointerException。
接口参数里 userId 为空。
代码没有做空值判断。
所以 500 可能来自 userId 空指针。
```

需要注意：LLM 的推理并不总稳定。复杂任务中，Agent 通常需要工具、测试、规则和人工确认来降低错误。

### 2.3 决策 Decision Making

决策是指 Agent 从多个可选动作中选择下一步。

常见决策包括：

- 是否需要调用工具
- 调用哪个工具
- 工具参数是什么
- 是否需要继续追问用户
- 是否应该停止
- 是否需要人工确认

例子：

```text
任务：修复测试失败
可选动作：
1. 直接猜测原因
2. 先运行测试
3. 查看最近提交
4. 读取相关文件

更合理的决策：先运行测试，拿到真实错误。
```

Agent 的可靠性，很大程度取决于它是否能做出正确的下一步决策。

### 2.4 执行 Action

执行是指 Agent 把决策转化成实际动作。

执行可以是：

- 调用搜索工具
- 查询数据库
- 读取文件
- 写代码
- 运行测试
- 调用业务 API
- 发送消息
- 创建任务

例子：

```text
Agent 决定运行测试：
python3 -m pytest

Agent 获取测试结果后，再决定下一步。
```

执行能力让 Agent 和普通聊天机器人拉开差距。

---

## 3. Agent 和 LLM 的区别

| 对比项 | LLM | Agent |
| --- | --- | --- |
| 核心能力 | 文本理解和生成 | 围绕目标执行任务 |
| 输入 | 用户消息、上下文 | 用户目标、环境状态、工具结果 |
| 输出 | 文本、结构化结果 | 文本、工具调用、任务执行结果 |
| 是否能行动 | 通常不能直接行动 | 可以通过工具行动 |
| 是否多步 | 可以回答多步推理 | 可以执行多步任务 |
| 是否依赖工具 | 不一定 | 通常强依赖工具 |
| 风险点 | 幻觉、格式不稳 | 幻觉、错误决策、工具误用、循环执行 |

一句更工程化的理解：

```text
LLM 是 Agent 的核心推理组件，但 Agent = LLM + 目标 + 状态 + 工具 + 控制流程 + 反馈循环。
```

---

## 4. Agent 的典型工作循环

可以用这个循环理解大多数 Agent：

```text
1. Goal：接收目标
2. Observe：观察当前信息
3. Think：分析下一步
4. Decide：选择动作
5. Act：执行动作
6. Observe：读取执行结果
7. Repeat：继续或停止
```

例子：代码修复 Agent

```text
Goal：修复测试失败
Observe：读取测试输出
Think：分析失败原因
Decide：查看相关源码
Act：读取文件
Observe：获得代码内容
Think：判断修改点
Decide：修改代码
Act：写入文件
Observe：重新运行测试
Repeat：通过则总结，失败则继续排查
```

---

## 5. Agent 的应用场景

### 5.1 开发助手

- 读代码
- 修 bug
- 写测试
- 生成文档
- 总结 PR
- 执行命令并根据结果调整

### 5.2 企业知识助手

- 查询知识库
- 总结制度文档
- 根据上下文回答问题
- 引用来源
- 必要时调用内部系统

### 5.3 数据分析 Agent

- 理解业务问题
- 选择指标
- 生成 SQL
- 查询数据库
- 解释结果
- 生成图表建议

这和 BI 背景非常契合。

### 5.4 客服和运营 Agent

- 识别用户意图
- 查询订单
- 判断规则
- 生成回复
- 必要时转人工

### 5.5 办公自动化 Agent

- 读取邮件
- 整理会议纪要
- 创建待办
- 查询日程
- 生成周报

---

## 6. 学习这一节时最容易混淆的点

### 6.1 Agent 不是“更会聊天的 LLM”

如果只是换一个 prompt，让模型回答更像人，这仍然主要是 LLM 应用。

Agent 的关键是：

- 有目标
- 有工具
- 有状态
- 能多步执行
- 能根据反馈调整

### 6.2 Agent 不等于完全自主

企业里的 Agent 往往需要边界：

- 哪些工具能调用
- 哪些数据能读取
- 哪些动作需要人工确认
- 出错时如何停止
- 是否允许修改真实数据

越接近生产环境，越不能让 Agent 无限制行动。

### 6.3 Agent 不是越复杂越好

简单任务用普通 LLM 或固定流程就够了。

适合 Agent 的任务通常具备：

- 步骤不完全固定
- 中间结果会影响下一步
- 需要调用工具
- 需要处理不确定性
- 需要多轮观察和调整

---

## 7. 官方资料提炼：真正有价值的 Agent 认知

这一节不是资料链接，而是把 OpenAI、LangChain、LangGraph 官方资料中对入门最有价值的内容提炼出来。

### 7.1 OpenAI 视角：Agent 是带运行能力的 LLM 应用

OpenAI Agents SDK 对 Agent 的理解可以概括为：

```text
Agent = LLM + instructions + tools + runtime behavior
```

其中：

- `LLM`：负责理解、生成、推理和选择下一步。
- `instructions`：告诉 Agent 角色、任务边界、工作规则和输出要求。
- `tools`：让 Agent 能访问外部世界，例如搜索、数据库、文件、业务 API。
- `runtime behavior`：运行时行为，例如 handoffs、guardrails、structured outputs、hooks、session。

这说明 Agent 不是一个单独的模型，而是一个工程系统。

如果只调用一次模型，让它返回一段文字，这通常只是 LLM 应用；如果模型能在运行过程中选择工具、执行动作、根据结果继续下一步，这才更接近 Agent。

### 7.2 LangChain 视角：Agent 是模型循环调用工具直到任务完成

LangChain 的 Agent 定义很适合初学者：

```text
Agent = model calling tools in a loop until the task is complete
```

可以拆成两步循环：

```text
1. Model call：模型根据当前上下文决定回答，或请求调用某个工具。
2. Tool execution：系统执行工具，把工具结果返回给模型。
```

这个循环会一直进行，直到模型判断任务完成，输出最终结果。

所以你理解 Agent 时，不要只看“模型回答了什么”，而要看：

- 模型拿到了哪些上下文
- 模型有哪些工具可用
- 模型为什么选择这个工具
- 工具返回了什么
- 模型如何根据工具结果继续下一步
- 最终什么时候停止

这就是 Agent 的核心运行机制。

### 7.3 Harness：Agent 外面那一圈工程控制

LangChain 里有一个很重要的说法：`Agent = Model + Harness`。

`Harness` 可以理解成“套在模型外面的工程控制层”，它负责：

- 给模型准备合适的 prompt
- 给模型提供可用工具
- 控制消息历史
- 控制结构化输出
- 处理工具调用结果
- 加入中间件、日志、监控、错误处理
- 在合适的时候停止循环

这对工程师很重要：Agent 开发不只是写 prompt，而是设计模型外面的控制系统。

面试时可以这样说：

```text
我理解的 Agent 不只是 LLM 本身，而是 LLM 加上一套运行框架。
这套框架负责上下文管理、工具调用、状态维护、错误处理和执行控制。
```

### 7.4 什么时候应该做 Agent

不是所有 AI 功能都应该做成 Agent。

适合 Agent 的任务通常有这些特征：

- 任务需要多步完成
- 每一步结果会影响下一步
- 需要调用外部工具或系统
- 输入信息不完整，需要边查边做
- 传统规则流程很难覆盖所有情况
- 任务中有一定不确定性，需要模型判断

不太适合 Agent 的任务：

- 固定分类
- 简单文本改写
- 单次摘要
- 简单问答
- 明确固定流程的表单处理

这些简单任务用一次 LLM 调用、普通工作流或固定规则通常更稳定。

一个实用判断标准：

```text
如果任务可以用固定步骤稳定完成，优先用普通流程。
如果任务需要根据中间结果动态决定下一步，再考虑 Agent。
```

### 7.5 Agent 的基础组件

一个基础 Agent 通常包含这些组件：

| 组件 | 作用 | 例子 |
| --- | --- | --- |
| Model | 理解任务并决定下一步 | GPT、Claude、Gemini、本地模型 |
| Instructions | 定义角色、规则、边界 | 你是数据分析助手，只能查询只读数据库 |
| Tools | 执行动作或获取信息 | 搜索、SQL 查询、文件读取、API 调用 |
| State | 保存当前任务状态 | 历史消息、工具结果、当前步骤 |
| Memory | 跨轮次或跨会话保存信息 | 用户偏好、历史任务摘要 |
| Guardrails | 安全和质量检查 | 输入过滤、输出校验、权限检查 |
| Orchestration | 控制流程 | 单 Agent、Manager、多 Agent handoff |
| Observability | 观察运行过程 | trace、日志、工具调用记录 |

初学时最重要的是前四个：

```text
Model + Instructions + Tools + State
```

没有工具，Agent 只能“说”；有了工具，它才能“做”。

没有状态，Agent 很难完成多步任务；有了状态，它才能知道自己做到哪一步。

### 7.6 工具分三类：Data、Action、Orchestration

OpenAI 的实践指南把工具分成三类，这个分类非常实用。

第一类：Data tools

用于获取上下文和信息。

例子：

- 查询数据库
- 搜索网页
- 读取 PDF
- 检索知识库
- 查询 CRM 或订单系统

第二类：Action tools

用于对外部系统执行动作。

例子：

- 发送邮件
- 创建工单
- 更新数据库记录
- 发起退款
- 推送消息

第三类：Orchestration tools

让一个 Agent 调用另一个 Agent，或者把任务转给专门的子 Agent。

例子：

- 研究 Agent
- 写作 Agent
- SQL Agent
- 客服退款 Agent

学习顺序建议：

```text
先学 Data tools，再学 Action tools，最后学 Orchestration tools。
```

原因是 Data tools 风险最低，主要读取信息；Action tools 会改变外部系统，必须考虑权限、确认和回滚；Orchestration tools 会引入多 Agent 协作，复杂度更高。

### 7.7 单 Agent 优先，不要一上来做 Multi-Agent

OpenAI 的实践经验里有一个很重要的原则：

```text
先尽量增强单个 Agent，再考虑拆成多个 Agent。
```

原因很现实：

- 单 Agent 更容易调试
- 单 Agent 更容易评测
- 单 Agent 的上下文更集中
- 多 Agent 会增加通信成本和错误传播
- 多 Agent 更难判断到底是哪一步出错

什么时候才考虑 Multi-Agent？

- 一个 Agent 的 instructions 已经变得非常复杂
- 工具太多，模型经常选错工具
- 不同任务领域差异很大
- 需要把专业能力拆给不同角色
- 某个子任务可以独立评测和复用

常见 Multi-Agent 模式有两种：

| 模式 | 说明 | 适合场景 |
| --- | --- | --- |
| Manager Pattern | 一个中心 Agent 调用多个专业 Agent 作为工具 | 希望统一入口、统一上下文 |
| Handoffs | 当前 Agent 把对话控制权交给另一个 Agent | 客服分流、专业领域转接 |

初学阶段你先掌握单 Agent 就够了。

### 7.8 Guardrails：Agent 必须有护栏

Agent 会调用工具、读取数据、甚至修改外部系统，所以必须有护栏。

Guardrails 可以分为几类：

- 输入护栏：检查用户输入是否越权、恶意、缺少必要信息。
- 工具护栏：限制 Agent 能调用哪些工具、能传什么参数。
- 输出护栏：检查最终回答是否符合格式、安全和业务规则。
- 权限护栏：不同用户只能访问自己有权限的数据。
- 人工确认：高风险动作执行前必须让人确认。

例子：

```text
用户：帮我把所有客户余额清零。
```

一个没有护栏的 Agent 可能会尝试调用数据库更新工具。

一个有护栏的 Agent 应该：

- 判断这是高风险写操作
- 检查用户权限
- 拒绝或要求人工确认
- 记录审计日志

所以生产级 Agent 的关键不是“让它更自由”，而是“让它在边界内可靠行动”。

### 7.9 Context Engineering：Agent 可靠性的核心

LangChain 的 context engineering 资料里有一个非常关键的观点：

Agent 失败通常有两类原因：

- 模型本身能力不够
- 没有把正确上下文以正确形式提供给模型

在很多实际问题中，第二类更常见。

也就是说，Agent 不靠谱，很多时候不是模型太差，而是：

- prompt 不清楚
- 工具描述不清楚
- 工具太多或太像
- 历史消息太乱
- 检索到的资料不相关
- 缺少业务规则
- 没有把用户权限传进去
- 没有把上一步工具结果整理好

AI 工程师很重要的一项工作就是：

```text
在正确的时间，把正确的信息、正确的工具、正确的格式交给模型。
```

这比单纯“写一个更厉害的 prompt”更重要。

### 7.10 Agent 的三类上下文

做 Agent 时，可以把上下文分成三类：

第一类：Model Context

模型本次调用能看到的内容。

包括：

- system prompt
- 用户消息
- 历史消息
- 可用工具列表
- 工具描述
- 输出格式要求

第二类：Tool Context

工具执行时能访问的内容。

包括：

- 用户 ID
- 权限信息
- 数据库连接
- API key
- 当前运行配置
- 业务环境变量

第三类：Lifecycle Context

Agent 在运行过程中，步骤之间如何处理信息。

包括：

- 日志
- trace
- 消息压缩
- 工具结果清洗
- guardrails
- 错误重试
- 状态保存

初学时你可以先这样记：

```text
Model Context 决定模型怎么想。
Tool Context 决定工具能做什么。
Lifecycle Context 决定整个 Agent 怎么稳定运行。
```

### 7.11 LangGraph 视角：Agent 需要可控的状态机

LangGraph 的价值在于：当 Agent 任务变长、状态变复杂、需要人工介入时，简单的 while loop 不够用了。

LangGraph 更像是一个 Agent 编排运行时，用来构建：

- 长时间运行的 Agent
- 有状态的 Agent
- 可恢复的 Agent
- 可人工介入的 Agent
- 可观测和可调试的 Agent

它强调几个能力：

- Persistence：任务失败或中断后，可以从状态恢复。
- Human-in-the-loop：人可以在任意步骤检查和修改状态。
- Memory：支持短期工作记忆和长期记忆。
- Debugging：可以看到 Agent 的执行路径、状态变化和工具调用。
- Deployment：支持更接近生产环境的长期运行工作流。

你现在不需要马上学 LangGraph API，但要先知道它解决的问题：

```text
普通 Agent loop 适合简单任务。
LangGraph 适合复杂、多步骤、有状态、需要控制和恢复的 Agent。
```

### 7.12 面试表达：一句话讲清 Agent

你可以这样回答：

```text
我理解的 AI Agent 不是单次调用大模型，而是以 LLM 为核心推理组件，
结合 instructions、tools、state、memory、guardrails 和 orchestration，
让系统能围绕一个目标进行多步决策和执行。
普通 LLM 主要负责生成内容，而 Agent 还能调用外部工具、观察结果、
根据中间状态继续调整，直到任务完成或触发停止条件。
```

如果面试官继续问“Agent 为什么容易不稳定”，可以答：

```text
主要原因有三类：一是模型本身推理和工具选择不稳定；
二是上下文工程没做好，比如工具描述不清、历史消息混乱、业务规则缺失；
三是工程控制不足，比如缺少状态管理、错误重试、guardrails、trace 和评测。
```

---

## 8. 本节检查题

1. 用自己的话解释什么是 AI Agent。
2. Agent 的感知能力可以来自哪些信息？
3. 推理和决策有什么区别？
4. 为什么说执行能力是 Agent 和普通 LLM 的关键区别？
5. Agent 和 LLM 的关系是什么？
6. 举一个 BI 场景里适合做成 Agent 的例子。
7. 为什么初学阶段建议先做单 Agent，而不是直接 Multi-Agent？
8. Data tools 和 Action tools 有什么区别？
9. Agent 失败时，为什么不应该第一反应就是“模型不行”？
10. LangGraph 主要解决 Agent 开发里的什么问题？

---

## 9. 本节资料来源

本笔记已提炼以下资料中的关键内容：

- [OpenAI Agents SDK: Agents](https://openai.github.io/openai-agents-python/agents/)
- [OpenAI: A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- [OpenAI: New tools for building agents](https://openai.com/index/new-tools-for-building-agents/)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Context Engineering in Agents](https://docs.langchain.com/oss/python/langchain/context-engineering)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)

学习方式：

1. 先读本笔记，理解概念。
2. 再看官方文档中的例子，把例子映射到本笔记的概念。
3. 后续写代码时，优先识别：model、instructions、tools、state、guardrails、orchestration。
