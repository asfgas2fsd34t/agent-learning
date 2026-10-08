# 07 ChatModel API 总览

> 来源：Spring AI 官方文档 `api/index.html`（1.1.x）。

## 学习目标

- 从章节地图视角把前 6 讲串起来
- 理解 ChatResponse / Generation / Metadata 的返回值结构
- 知道每个能力对应文档哪一节，方便回查

## 1. 核心心智模型

```text
ChatModel API 参考 = Spring AI 与模型交互的全部抽象
          ┌── ChatClient（01）：门面 + fluent API
ChatModel ┤── Prompt/Message（04）：输入结构
          ├── Advisors（02/03）：横切拦截
          ├── Structured Output（05）：强类型输出
          ├── Multimodality（06）：多模态输入
          └── Tool Calling（09）：外部能力
```

## 2. 返回值结构：ChatResponse → Generation

```java
ChatResponse response = chatClient.prompt().user("hi").call().chatResponse();

// 结构
// ChatResponse
// ├── metadata: ChatResponseMetadata（model、usage token 统计等）
// └── generations: List<Generation>
//     └── Generation
//         ├── output: AssistantMessage（text、metadata）
//         └── metadata: ChatGenerationMetadata（finishReason 等）

Generation first = response.getResult();          // = getResults().get(0)
String text = first.getOutput().getText();
String model = response.getMetadata().getModel();
Usage usage = response.getMetadata().getUsage();  // promptTokens / completionTokens
```

要点：

- `getResults()` 返回 **List\<Generation\>**——多数情况 1 条；n>1 多候选时多条
- `getResult()` 是取第一条的快捷方式
- finish reason（stop / tool_calls / length）在 `ChatGenerationMetadata` 里，工具循环（09）要靠它判断

## 3. 章节地图（文档目录 → 本笔记）

| 文档节 | 本笔记 | 一句话 |
|--------|--------|--------|
| ChatClient | 01 | 流式门面、四段式链式调用 |
| Advisors | 02 | 栈式拦截器 |
| Recursive Advisors | 03 | 递归重试/工具循环 |
| Prompt | 04 | List\<Message\> + ChatOptions |
| Structured Output | 05 | entity() 强类型 |
| Multimodality | 06 | Media 附件 |
| Chat Model API（本节） | 07 | ChatResponse 结构总览 |
| Chat Memory | 08 | 会话记忆 |
| Tools | 09 | 工具调用 |
| Models（各家提供商） | — | 各模型专章，用到再查 |
| Embeddings / RAG | 后续 | 检索增强三件套 |
| Functions（旧称） | — | 1.x 统一叫 Tools |

## 4. 双层 API 速查

```text
高层：ChatClient.prompt().user(...).call().content()
底层：chatModel.call(new Prompt(List.of(new UserMessage(...))))
流式高层：...stream().content()          → Flux<String>
流式底层：chatModel.stream(prompt)       → Flux<ChatResponse>
结构化：...call().entity(Type)           → T
完整响应：...call().chatResponse()       → ChatResponse
```

## 5. 生产边界

- 业务代码拿 `content()`/`entity()` 就够；日志、审计、计费才碰 `chatResponse()` 的 metadata
- token 用量从 `response.getMetadata().getUsage()` 取，用于成本监控
- 底层 Prompt API 主要给框架内部/Advisor/工具循环用，业务首选 ChatClient
