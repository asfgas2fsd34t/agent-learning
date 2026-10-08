# Spring AI 开发实战学习路径

## 1. 整理说明

本目录按照 Spring AI 官方文档 1.1.x（`docs.spring.io/spring-ai/reference/1.1/`）逐页学习整理。笔记不是逐页翻译，而是提炼每页的重点、把示例都提炼出来，并保留学习过程中展开的概念问答和完整实战案例。

文档版本说明：官方文档没有 1.1.2 的独立版本页，`/reference/1.1/` 对应 1.1.x 最新补丁版（当前为 1.1.8）；最新稳定版是 2.0.1。看文档时可以用 Chrome 的整页翻译辅助阅读。

```text
01 ChatClient 流式 API
02 Advisor 体系
03 递归 Advisor
04 Prompt 与 Message
05 结构化输出
06 多模态
07 ChatModel API 总览
08 聊天记忆
09 工具调用（Tool Calling）
10 概念问答集
11 实战案例集
12 MCP（Model Context Protocol）
13 MCP Client Boot Starter
14 构建 MCP Server
15 RAG（检索增强生成）
```

## 2. 学习目标

完成本阶段后，应能够：

- 使用 ChatClient 流式 API 组织 prompt、call/stream、结构化输出
- 理解 Advisor 栈式拦截机制，能自定义 CallAdvisor / StreamAdvisor
- 理解递归 Advisor（`chain.copy(this)`）的质量门等模式
- 掌握 Prompt = List\<Message\> + ChatOptions 的底层模型
- 使用 Structured Output Converter 获取强类型返回值
- 掌握 Chat Memory 与 Chat History 的边界，能自定义压缩记忆
- 使用 `@Tool` 等三种方式定义工具，理解 Tool Calling 三种执行模式

## 3. 章节说明

| 章节 | 对应文档页 | 核心产出 |
|------|-----------|---------|
| 01 | api/chatclient.html | ChatClient 四段式链式调用 |
| 02 | api/advisors.html | BaseAdvisor vs 手工挡、流式打码案例 |
| 03 | api/advisors-recursive.html | QualityGateAdvisor 质量门案例 |
| 04 | api/prompt.html | Message 四角色、PromptTemplate |
| 05 | api/structured-output-converter.html | entity() 用法、泛型擦除对策 |
| 06 | api/multimodality.html | Media 与多模态消息 |
| 07 | api/index.html | ChatResponse/Generation 体系地图 |
| 08 | api/chat-memory.html | SummarizingChatMemory、PG 存储、多数据源 |
| 09 | api/tools.html | @Tool 三种定义、三种执行模式 |
| 10 | 学习过程问答 | 概念辨析（BaseAdvisor、generations、泛型擦除等） |
| 11 | 学习过程产出 | 完整可运行案例代码集 |
| 12 | api/mcp/ 章节 | MCP 架构、Starter、注解、Client 特性 |
| 13 | api/mcp/mcp-client-boot-starter-docs.html | Client Starter 配置与四大扩展点 |
| 14 | mcp-server-boot-starter + mcp-annotations-server | 构建 MCP Server 五步法与四类注解 |
| 15 | retrieval-augmented-generation + etl-pipeline | RAG 两半闭环与四阶段模块 |

## 4. 学习方法

每页的固定套路：**提炼重点 + 把示例都提炼出来 + 中文讲解 + 与前文串联**。建议按编号顺序阅读，10、11 是随时可查的速查与案例库。
