# Agent 架构模式笔记

## 学习目标

学完本节，需要能讲清楚：

- ReAct 是什么，为什么它是最经典的 Agent 模式
- Plan and Execute 为什么要把“规划”和“执行”拆开
- Reflection 反思模式如何让 Agent 自我修正
- Multi-Agent 为什么要拆多个 Agent，以及什么时候不该拆
- 不同架构模式分别适合什么场景

一句话版本：

**Agent 架构模式，本质上是在回答一个问题：让 LLM 以什么样的流程思考、调用工具、处理反馈、修正错误，并最终完成任务。**

---

## 1. 为什么需要 Agent 架构模式

普通 LLM 调用通常是：

```text
用户输入 -> 模型生成 -> 返回结果
```

这适合：

- 问答
- 总结
- 改写
- 分类
- 简单抽取

但 Agent 任务通常更复杂：

- 需要查资料
- 需要调用工具
- 需要多步执行
- 中间结果会影响下一步
- 可能失败，需要重试或修正
- 任务可能要拆成多个子任务

所以 Agent 不能只靠“单次生成”，需要一套运行模式。

常见模式包括：

```text
ReAct：边思考边行动
Plan and Execute：先规划再执行
Reflection：执行后反思和改进
Multi-Agent：多个 Agent 分工协作
```

这些模式不是互斥的。真实系统里经常组合使用：

```text
Plan and Execute + ReAct
ReAct + Reflection
Multi-Agent + Handoff
RAG + ReAct + Guardrails
```

---

## 2. ReAct：Reasoning and Acting

### 2.1 ReAct 解决什么问题

ReAct 来自论文《ReAct: Synergizing Reasoning and Acting in Language Models》。

它的核心思想是：

```text
让模型交替进行推理和行动。
```

也就是：

```text
Thought -> Action -> Observation -> Thought -> Action -> Observation -> Final Answer
```

中文可以理解为：

```text
思考 -> 调用工具 -> 观察结果 -> 继续思考 -> 再调用工具 -> 得出答案
```

传统 Chain-of-Thought 只让模型“想”，但不让模型查外部信息；普通工具调用只让模型“做”，但缺少明确推理轨迹。

ReAct 把二者结合起来：

- Reasoning：帮助模型分析目标、维护计划、处理异常
- Acting：帮助模型查询外部环境、获取新信息、验证判断

### 2.2 ReAct 的运行流程

一个典型 ReAct 流程：

```text
用户问题：某个接口为什么报 500？

Thought：我需要先查看错误日志。
Action：调用日志查询工具。
Observation：日志显示 NullPointerException。

Thought：需要定位是哪一行代码空指针。
Action：读取相关源码。
Observation：userId 没有判空。

Thought：可能是请求参数缺少 userId。
Action：查看请求样例。
Observation：请求里 userId 为空。

Final Answer：500 的直接原因是 userId 为空导致空指针，建议增加参数校验和友好错误返回。
```

可以看到，ReAct 的关键不是一次性想出完整答案，而是边查边想。

### 2.3 ReAct 的优点

- 适合信息不完整的任务
- 能通过工具减少幻觉
- 推理过程更容易观察
- 中间结果能影响下一步
- 适合搜索、问答、排查、简单工具调用任务

### 2.4 ReAct 的缺点

- 容易多次调用工具，成本和延迟更高
- 工具描述不清时，容易选错工具
- 模型可能陷入循环
- 对长任务缺少全局规划
- 每一步都让模型重新判断，稳定性不如固定流程

### 2.5 适合 ReAct 的场景

适合：

- 查资料回答问题
- 调用搜索工具
- 查询数据库
- 排查错误
- 根据工具结果逐步分析
- 任务步骤不长，但需要边查边判断

不太适合：

- 超长任务
- 明确需要先制定完整计划的任务
- 高风险执行动作
- 需要强审计、强控制的生产流程

### 2.6 学习 ReAct 时要记住

ReAct 的本质是：

```text
用推理决定行动，用行动补充推理。
```

面试表达：

```text
ReAct 是一种让 Agent 交替进行 Reasoning 和 Acting 的模式。
模型先根据目标和上下文进行思考，再选择工具执行动作，
拿到 Observation 后继续推理，直到可以给出最终答案。
它适合需要边获取信息边决策的任务，但要注意循环、成本和工具误用问题。
```

---

## 3. Plan and Execute：先规划再执行

### 3.1 Plan and Execute 解决什么问题

ReAct 是一步一步边想边做，适合动态探索。

但如果任务很复杂，只靠一步一步反应，容易出现：

- 缺少全局目标
- 做一步看一步
- 工具调用次数多
- 中间步骤偏离主线
- 难以并行
- 成本和延迟较高

Plan and Execute 的思路是：

```text
先让 Planner 生成计划，再让 Executor 按计划执行。
```

也就是：

```text
用户目标 -> Planner 拆解任务 -> Executor 执行每个步骤 -> 汇总结果
```

### 3.2 Plan and Execute 的基本结构

常见结构：

```text
Planner：负责理解目标，拆成多个步骤。
Executor：负责执行具体步骤，可能调用工具。
Replanner：如果执行失败或环境变化，重新调整计划。
```

示例：

```text
任务：分析本月销售额下降原因。

Planner 生成计划：
1. 查询本月和上月总销售额
2. 按渠道拆分销售额变化
3. 按地区拆分销售额变化
4. 检查订单量、客单价、转化率
5. 总结主要原因

Executor 执行：
- 第一步调用 SQL 查询工具
- 第二步继续查询渠道维度
- 第三步查询地区维度
- ...

最终输出：
- 销售额下降主要来自 A 渠道和华东地区
- 订单量下降比客单价下降影响更大
```

### 3.3 Plan and Execute 的优点

- 有全局规划
- 更适合长任务
- 更容易审计每一步
- 可以限制每一步工具权限
- 某些步骤可以并行
- 比纯 ReAct 更容易控制成本

### 3.4 Plan and Execute 的缺点

- 初始计划如果错了，后面会跟着错
- 环境变化时需要重新规划
- 简单任务会显得过重
- Planner 和 Executor 边界设计不好时，会互相干扰
- 如果计划太粗，Executor 仍然要大量推理
- 如果计划太细，系统会变僵硬

### 3.5 适合 Plan and Execute 的场景

适合：

- 长任务
- 数据分析
- 调研报告
- 代码迁移
- 多步骤排查
- 可以先拆解再执行的任务
- 需要审计步骤的企业流程

不太适合：

- 简单问答
- 简单分类
- 一两步就能完成的工具调用
- 环境变化极快、必须随时反应的任务

### 3.6 ReAct 和 Plan and Execute 的区别

| 对比项 | ReAct | Plan and Execute |
| --- | --- | --- |
| 核心方式 | 边想边做 | 先规划再执行 |
| 适合任务 | 中短任务、动态查询 | 长任务、复杂任务 |
| 全局视角 | 较弱 | 较强 |
| 灵活性 | 高 | 中等，依赖重规划 |
| 可控性 | 中等 | 更高 |
| 成本 | 可能较高 | 可通过计划控制 |
| 风险 | 循环、工具误用 | 计划错误、执行僵硬 |

面试表达：

```text
Plan and Execute 把 Agent 的规划和执行拆开。
Planner 先把复杂目标拆成步骤，Executor 再逐步执行。
它比 ReAct 更适合长任务和需要审计的流程，但要处理计划错误和重规划问题。
```

---

## 4. Reflection：反思模式

### 4.1 Reflection 解决什么问题

普通 Agent 执行完一步或输出答案后，可能存在问题：

- 答案不完整
- 推理有漏洞
- 工具调用失败
- 代码生成后运行失败
- SQL 结果解释不合理
- 初稿质量不高

Reflection 的核心思想是：

```text
让 Agent 对自己的输出或执行结果进行检查、批评、总结，并用反馈改进下一轮。
```

Reflexion 论文里一个重要点是：Agent 不一定需要通过更新模型参数来学习，也可以通过“语言形式的反馈”和“反思记忆”来改善后续表现。

也就是：

```text
执行 -> 获得反馈 -> 反思失败原因 -> 保存反思 -> 下一次用反思指导行动
```

### 4.2 Reflection 的基本流程

常见流程：

```text
1. Generator：生成初始答案或执行动作
2. Critic：检查结果，指出问题
3. Reflector：总结改进建议
4. Generator：根据反馈重新生成
5. Repeat：直到通过检查或达到次数上限
```

代码生成场景：

```text
Agent 生成代码
运行测试
测试失败
Agent 读取错误信息
反思：失败原因是函数没有处理空输入
修改代码
再次运行测试
通过后输出总结
```

RAG 场景：

```text
检索文档
生成答案
检查答案是否引用了来源
发现依据不足
重新检索或回答“资料不足”
```

### 4.3 Reflection 的优点

- 能提升输出质量
- 能利用工具反馈修正错误
- 适合代码、写作、问答、RAG 自校验
- 比单次生成更稳
- 能保留失败经验，减少重复错误

### 4.4 Reflection 的缺点

- 会增加 token 成本和延迟
- Critic 自己也可能判断错
- 反思内容可能变成噪声
- 可能出现“自我感觉良好”的假检查
- 如果没有外部验证，只靠模型自评不可靠

### 4.5 适合 Reflection 的场景

适合：

- 代码生成后运行测试
- SQL 生成后校验语法
- RAG 回答后检查引用
- 文案初稿润色
- 多轮改进的复杂输出
- 有明确反馈信号的任务

不太适合：

- 强实时任务
- 简单分类
- 没有明确评判标准的任务
- 高风险动作执行前只靠模型自我反思

### 4.6 Reflection 的关键原则

Reflection 最好结合外部反馈，而不是纯自言自语。

外部反馈可以是：

- 测试结果
- 编译错误
- SQL 执行结果
- 规则校验
- 人工评价
- 检索评分
- JSON schema 校验

面试表达：

```text
Reflection 是让 Agent 对自己的输出或执行结果进行批评和修正的模式。
它通常包括生成、检查、反思、再生成几个环节。
我认为它最好和外部验证结合，比如测试结果、SQL 校验、引用检查，
否则纯模型自评容易出现误判。
```

---

## 5. Multi-Agent：多 Agent 协作

### 5.1 Multi-Agent 解决什么问题

单个 Agent 能处理很多任务，但当任务越来越复杂时，会遇到问题：

- instructions 太长
- 工具太多
- 模型经常选错工具
- 不同任务需要不同专业知识
- 一个 Agent 的上下文越来越乱
- 不同子任务需要不同权限

Multi-Agent 的思路是：

```text
把复杂任务拆给多个专业 Agent，由它们协作完成。
```

比如：

```text
Supervisor Agent：负责理解用户目标和分派任务
SQL Agent：负责生成和执行 SQL
Chart Agent：负责选择图表
Report Agent：负责总结业务结论
```

### 5.2 Multi-Agent 的常见模式

#### 模式一：Supervisor / Manager

一个主管 Agent 负责调度多个子 Agent。

```text
用户 -> Supervisor -> 子 Agent A / 子 Agent B / 子 Agent C -> Supervisor 汇总
```

适合：

- 希望统一入口
- 需要集中控制任务流
- 子任务边界比较清楚
- 需要最终统一汇总

例子：

```text
用户：分析销售额下降原因。
Supervisor 判断需要：
- SQL Agent 查询数据
- Analysis Agent 分析原因
- Report Agent 生成报告
```

#### 模式二：Handoff

一个 Agent 把控制权交给另一个 Agent。

```text
客服 Agent -> 退款 Agent
通用助手 -> 数据分析 Agent
数据分析 Agent -> SQL Agent
```

适合：

- 用户意图需要转接
- 不同 Agent 负责不同业务域
- 对话上下文需要继续传递

#### 模式三：协作讨论

多个 Agent 分别提出观点，再由一个 Agent 汇总。

适合：

- 方案评审
- 多角度分析
- 复杂写作
- 安全审查

但这个模式成本高，也容易产生空转，不建议初学阶段优先用。

### 5.3 Multi-Agent 的优点

- 专业职责清晰
- 每个 Agent 的 prompt 更短
- 工具权限可以隔离
- 子任务可以复用
- 某些任务可以并行
- 更贴近组织分工

### 5.4 Multi-Agent 的缺点

- 调试复杂
- 成本更高
- 延迟更高
- Agent 之间可能传错信息
- 错误会在链路中放大
- 需要设计通信协议和状态传递
- 很容易为了“看起来高级”而过度设计

### 5.5 什么时候才应该用 Multi-Agent

先不要为了学概念就直接 Multi-Agent。

只有出现这些问题时再考虑：

- 单 Agent 工具太多，选错工具频繁
- 单 Agent instructions 过长且混乱
- 子任务边界天然独立
- 不同子任务需要不同权限
- 子 Agent 可以独立测试
- 需要明确的业务转接流程

如果单 Agent 能稳定完成，就不要拆。

面试表达：

```text
Multi-Agent 是把复杂任务拆给多个专业 Agent 协作完成。
常见模式有 Supervisor 和 Handoff。
它的优势是职责清晰、工具和权限可以隔离，但会增加调试、成本和状态管理复杂度。
所以我会优先从单 Agent 做起，只有当工具过多、任务边界清晰或权限需要隔离时才拆成多 Agent。
```

---

## 6. 四种模式怎么选择

| 任务特征 | 推荐模式 |
| --- | --- |
| 需要边查边回答 | ReAct |
| 长任务，需要先拆步骤 | Plan and Execute |
| 输出需要自查和改进 | Reflection |
| 子任务边界清晰、工具很多 | Multi-Agent |
| 简单问答或分类 | 不一定需要 Agent |
| 高风险写操作 | Agent + Guardrails + Human-in-the-loop |

更工程化的选择顺序：

```text
1. 能用普通 LLM 调用解决，就不要上 Agent。
2. 需要工具和动态反馈，再考虑 ReAct。
3. 任务很长，再考虑 Plan and Execute。
4. 结果质量需要提升，再加 Reflection。
5. 单 Agent 变得太复杂，再拆 Multi-Agent。
```

### 6.1 四种模式的关键区分点

最核心的区分不是“哪个更高级”，而是看任务需要什么控制方式。

| 关键问题 | 如果答案是 | 更倾向 |
| --- | --- | --- |
| 任务是否需要边查边决定下一步？ | 是 | ReAct |
| 任务是否一开始就能拆成多个清晰步骤？ | 是 | Plan and Execute |
| 结果是否需要检查、修改、再生成？ | 是 | Reflection |
| 是否有多个职责明显不同的专业角色？ | 是 | Multi-Agent |
| 是否只是简单问答、总结、分类？ | 是 | 普通 LLM 调用 |

可以用四句话记：

```text
ReAct 解决“边查边做”。
Plan and Execute 解决“先拆再做”。
Reflection 解决“做完再改”。
Multi-Agent 解决“多人分工”。
```

### 6.2 判断模式的五个维度

#### 维度一：步骤是否固定

如果步骤固定，例如：

```text
读取文本 -> 分类 -> 输出 JSON
```

通常不需要 Agent。

如果步骤不固定，例如：

```text
先看报错，报错是什么再决定查日志、查代码还是查配置
```

更适合 ReAct。

#### 维度二：是否需要全局规划

如果任务一开始就知道要拆成多个阶段，例如：

```text
调研竞品 -> 提取卖点 -> 生成报告 -> 输出建议
```

更适合 Plan and Execute。

如果任务很短，只需要查一两次工具，ReAct 就够了。

#### 维度三：是否有明确反馈信号

如果有明确反馈，例如：

- 测试通过/失败
- SQL 执行成功/失败
- JSON schema 校验通过/失败
- 引用来源是否存在

可以加入 Reflection。

如果没有明确反馈，只让模型“自我反思一下”，价值有限，甚至可能引入噪声。

#### 维度四：是否需要角色分工

如果一个 Agent 的工具越来越多、规则越来越长、职责越来越杂，就可以考虑 Multi-Agent。

但只要单 Agent 能稳定完成，就先不要拆。

#### 维度五：是否有风险动作

如果 Agent 要执行写操作，例如：

- 改数据库
- 发邮件
- 创建订单
- 发起退款
- 删除文件

架构模式之外还必须加：

```text
Guardrails + 权限控制 + Human-in-the-loop + 审计日志
```

这不是 ReAct、Plan and Execute、Multi-Agent 本身能自动解决的。

### 6.3 例子一：查询“某个 API 为什么报错”

需求：

```text
帮我看看这个接口为什么报 500。
```

更适合：ReAct

原因：

- 一开始不知道问题在哪里
- 需要先看日志
- 根据日志再决定看代码、配置、数据库还是请求参数
- 中间观察结果会影响下一步

可能流程：

```text
Thought：先查错误日志。
Action：查询日志。
Observation：发现 NullPointerException。
Thought：需要看相关代码。
Action：读取接口代码。
Observation：发现 userId 未判空。
Final Answer：定位原因并给修复建议。
```

为什么不是 Plan and Execute？

因为一开始无法制定稳定完整计划，必须根据日志动态决定。

为什么可以加 Reflection？

如果 Agent 修改了代码并运行测试，就可以在测试失败后反思和修正。

### 6.4 例子二：生成一份“本月经营分析报告”

需求：

```text
帮我生成一份本月经营分析报告，包括销售趋势、渠道表现、地区表现、异常原因和建议。
```

更适合：Plan and Execute + ReAct

原因：

- 这是长任务
- 可以先拆成清晰步骤
- 每个步骤内部可能还需要查数据

可能计划：

```text
1. 查询本月和上月核心指标
2. 分析销售趋势
3. 分析渠道维度
4. 分析地区维度
5. 检查异常波动
6. 生成报告结论
```

执行每一步时，可以用 ReAct：

```text
Thought：渠道维度需要查 GMV 和订单数。
Action：执行 SQL。
Observation：A 渠道 GMV 下降明显。
Thought：继续查 A 渠道订单量和客单价。
```

为什么不是纯 ReAct？

纯 ReAct 容易做一步看一步，长报告可能漏掉重要维度。

为什么可以加 Reflection？

报告生成后可以检查：

- 是否每个结论都有数据支持
- 是否遗漏计划中的章节
- 是否把相关性说成因果

### 6.5 例子三：把用户评论分类为“好评/差评/中立”

需求：

```text
把这 100 条评论分成好评、差评、中立。
```

更适合：普通 LLM 调用，不一定需要 Agent

原因：

- 步骤固定
- 不需要工具
- 不需要动态决策
- 不需要多 Agent

流程：

```text
输入评论 -> 模型分类 -> 输出 JSON
```

如果要求严格，可以加：

```text
结构化输出 + schema 校验 + 抽样人工复核
```

为什么不用 ReAct？

没有“边查边决定下一步”的需求。

为什么不用 Multi-Agent？

任务边界太简单，拆多个 Agent 只会增加复杂度。

### 6.6 例子四：代码生成并确保测试通过

需求：

```text
帮我实现一个功能，并确保测试通过。
```

更适合：ReAct + Reflection

原因：

- 需要读代码、写代码、运行测试
- 测试结果会决定下一步
- 测试失败后需要反思原因并修改

流程：

```text
ReAct：
Thought：先看相关文件。
Action：读取代码。
Observation：了解现有结构。
Thought：实现功能。
Action：修改代码。
Observation：代码已修改。

Reflection：
Action：运行测试。
Observation：测试失败。
Reflect：失败原因是边界情况没处理。
Action：修复代码。
Observation：测试通过。
```

为什么不是 Plan and Execute？

如果功能很小，没必要先做复杂计划。

如果是大型迁移，比如“把整个模块从 A 框架迁到 B 框架”，则更适合 Plan and Execute。

### 6.7 例子五：客服系统处理退款

需求：

```text
用户要求退款，系统需要判断订单状态、退款规则，并在符合条件时发起退款。
```

更适合：ReAct + Guardrails + Human-in-the-loop

如果业务域很复杂，可以演进到 Multi-Agent。

原因：

- 需要查询订单
- 需要判断规则
- 可能需要执行高风险动作
- 退款属于写操作，必须有权限和确认

流程：

```text
Thought：需要查询订单状态。
Action：查询订单。
Observation：订单已发货。
Thought：需要查询退款规则。
Action：查询规则。
Observation：已发货订单需人工审核。
Decision：转人工或请求确认，不能自动退款。
```

什么时候拆 Multi-Agent？

如果客服系统有多个复杂业务域：

- 退款 Agent
- 物流 Agent
- 账号 Agent
- 投诉 Agent

且每个业务域规则、工具、权限都不同，就可以用 Handoff。

### 6.8 例子六：企业知识库问答

需求：

```text
员工问：年假怎么计算？
```

更适合：RAG，通常不一定需要 Agent

原因：

- 主要是检索资料并回答
- 步骤相对固定

流程：

```text
检索制度文档 -> 拼接上下文 -> 模型回答 -> 返回引用来源
```

什么时候用 ReAct？

如果问题需要跨多个系统查询，比如：

```text
我今年还能休几天年假？
```

这时需要：

- 查制度
- 查员工入职时间
- 查已休假记录
- 计算剩余额度

这就更像 ReAct，因为需要调用多个工具并根据结果继续判断。

### 6.9 例子七：复杂数据分析助手

需求：

```text
帮我分析为什么最近转化率下降，并给出可行动建议。
```

更适合：Plan and Execute + ReAct + Reflection

原因：

- 任务较长，需要先规划分析路径
- 每一步需要查询数据
- 最终结论需要检查是否有证据

推荐结构：

```text
Planner：
1. 确认转化率定义
2. 查询整体趋势
3. 按渠道拆分
4. 按地区拆分
5. 按设备拆分
6. 检查异常时间点
7. 汇总原因和建议

Executor：
每一步用 ReAct 查询数据和解释结果。

Reflector：
检查结论是否有数据支持，是否遗漏关键维度。
```

为什么第一版不建议 Multi-Agent？

因为你还需要先验证单 Agent 是否能稳定完成：

- 指标理解
- SQL 生成
- 数据解释
- 报告输出

等单 Agent 工具太多、职责太杂，再拆成 SQL Agent、Metric Agent、Analysis Agent。

### 6.10 最实用的选择口诀

可以这样快速判断：

```text
简单固定任务：普通 LLM 调用。
需要查工具、边查边判断：ReAct。
任务很长、先能拆步骤：Plan and Execute。
结果要校验和改进：Reflection。
职责太多、工具太多、权限不同：Multi-Agent。
涉及写操作：一定加 Guardrails 和人工确认。
```

---

## 7. BI 场景下的架构模式理解

你有 BI 背景，可以这样联系：

### 7.1 ReAct in BI

用户问：

```text
为什么本月 GMV 下降？
```

ReAct 流程：

```text
Thought：先查整体 GMV 环比。
Action：查询 SQL。
Observation：GMV 下降 12%。
Thought：需要按渠道拆分。
Action：查询渠道维度。
Observation：A 渠道下降最多。
Thought：继续查订单量和客单价。
Action：查询指标。
Final Answer：主要原因是 A 渠道订单量下降。
```

### 7.2 Plan and Execute in BI

先生成分析计划：

```text
1. 查整体趋势
2. 查渠道贡献
3. 查地区贡献
4. 查订单量、客单价、转化率
5. 总结原因
```

再一步步执行。

### 7.3 Reflection in BI

生成分析报告后检查：

- 是否引用了数据
- 是否把相关性说成因果
- 是否遗漏关键维度
- SQL 是否只读
- 结论是否有证据支持

### 7.4 Multi-Agent in BI

可以拆成：

```text
SQL Agent：负责查数
Metric Agent：负责解释指标口径
Analysis Agent：负责分析原因
Chart Agent：负责推荐图表
Supervisor Agent：负责调度和汇总
```

但第一版不要这么拆，先从单 Agent 做起。

---

## 8. 学习检查题

1. ReAct 的核心循环是什么？
2. ReAct 为什么能减少幻觉？
3. Plan and Execute 为什么适合长任务？
4. Reflection 为什么最好结合外部反馈？
5. Multi-Agent 相比单 Agent 最大的代价是什么？
6. 如果你要做一个 BI 分析 Agent，第一版应该优先用哪种模式？为什么？
7. 什么情况下不应该用 Agent？
8. 什么情况下应该从单 Agent 拆成 Multi-Agent？

---

## 9. 面试速记

### 9.1 ReAct

```text
ReAct 是让 Agent 交替进行推理和行动的模式。
它通过 Thought、Action、Observation 的循环，
让模型能边查资料、边调用工具、边修正判断。
```

### 9.2 Plan and Execute

```text
Plan and Execute 把规划和执行拆开。
Planner 先拆解任务，Executor 再执行步骤。
它适合长任务和需要审计的流程，但需要处理计划错误和重规划。
```

### 9.3 Reflection

```text
Reflection 是让 Agent 对自己的输出或执行结果进行批评和修正。
它适合代码生成、RAG 自校验、SQL 校验等有明确反馈的任务。
```

### 9.4 Multi-Agent

```text
Multi-Agent 是多个专业 Agent 分工协作。
它能隔离职责、工具和权限，但会增加调试、成本和状态管理复杂度。
```

---

## 10. 资料来源

本笔记提炼自以下资料：

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Google Research: ReAct](https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/)
- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)
- [LangChain: Plan-and-Execute Agents](https://www.langchain.com/blog/planning-agents)
- [LangChain: Reflection Agents](https://www.langchain.com/blog/reflection-agents)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph Supervisor Reference](https://reference.langchain.com/python/langgraph-supervisor)
- [OpenAI: A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
