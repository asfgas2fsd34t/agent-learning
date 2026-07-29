# LangChain 开发实战

本目录学习使用 LangChain 构建单 Agent。practice 按“一个练习覆盖一个完整能力组”的方式组织，不要求每个 note 文件都对应一个目录。

## 主线练习

1. [练习 01：LangChain 基础](01-langchain-basics/README.md)（对应 00、01、02、04、06）
2. [练习 02：LangSmith 可观测性](02-langsmith/README.md)（对应 03）
3. [练习 03：Runnable 与 LCEL 深入](03-langchain-runnables/README.md)（对应 10）
4. [练习 04：LangChain Tools](04-langchain-tools/README.md)（对应 05）
5. [练习 05：LangChain Agent](05-langchain-agent/README.md)（对应 07）
6. [练习 06：上下文与记忆](06-langchain-memory/README.md)（对应 09）
7. [练习 07：生产级工具集成](07-production-tools/README.md)（对应 11）
8. [练习 08：Agent 安全与中间件](08-agent-middleware/README.md)（对应 08、12）
9. [练习 09：Agent 调试、评测与性能优化](09-agent-evaluation/README.md)（对应 13）

## Note 与 Practice 的关系

```text
00 Pydantic 前置知识       -> 01 LangChain 基础中的 structured.py
01 LangChain 概述          -> 01 LangChain 基础
02 模型的创建与调用         -> 01 LangChain 基础中的 model.py / messages.py
03 LangSmith 的使用         -> 02 LangSmith 可观测性
04 Message 与提示词模板    -> 01 LangChain 基础中的 messages.py / chains.py
05 Tools                  -> 04 LangChain Tools
06 结构化输出              -> 01 LangChain 基础中的 structured.py
07 智能体                  -> 05 LangChain Agent
08 中间件                  -> 08 Agent 安全与中间件
09 上下文与记忆            -> 06 上下文与记忆
10 Runnable 与 LCEL        -> 03 Runnable 与 LCEL 深入
11 生产级工具集成          -> 07 生产级工具集成
12 Agent 安全与业务边界    -> 08 Agent 安全与中间件中的安全校验
13 调试评测与性能优化      -> 09 Agent 调试、评测与性能优化
```

一个练习可以覆盖多个基础 note，但 README 必须明确覆盖范围；一个 note 如果没有独立练习，也必须指出它落在哪个代码入口中。
