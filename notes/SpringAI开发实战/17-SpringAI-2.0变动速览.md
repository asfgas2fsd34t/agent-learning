# 17 Spring AI 2.0 变动速览

> 来源：官方 upgrade-notes（`reference/upgrade-notes.html`）与 v2.0.0 / v2.0.1 Release Notes（2026-06 / 2026-08）。当前主线学习用 1.1.x，本章供升级前瞻。

## 学习目标

- 知道 2.0 的基线变化（Spring Boot 4、MCP SDK 2.0）
- 掌握工具调用大重构的要点（对 09 章写法影响最大）
- 知道 Chat Memory 收紧的两个破坏点
- 升级时能对着清单自查

## 1. 核心结论

```text
2.0 不是推倒重来：概念模型（ChatClient/Advisor/Tool/Memory/RAG/MCP）全部保留
主线变化一句话：工具执行循环从 ChatModel 收归 ToolCallingAdvisor 统一管理，API 全面严格化
你现在学 1.1.x 的概念知识在 2.0 全部有效，主要是 API 写法迁移
```

## 2. 基线升级

- **Spring Boot 4.x**（2.0.0 用 4.1.0）——最大的隐形门槛
- MCP Java SDK 升到 2.0.0
- OpenAiChatModel 只用 Jackson 2

## 3. 工具调用大重构（影响最大）

### 3.1 ChatModel 内部工具循环被移除

1.x 里 `chatModel.call(prompt)` 带工具会自动执行 tool_calls 并循环；2.0 **所有模型实现（OpenAI/Anthropic/Ollama/DeepSeek/Bedrock/MiniMax/Mistral/Google GenAI）都移除了内部循环**——`call()/stream()` 返回原始响应，工具不自动执行。

```java
// 2.0 推荐：ChatClient 自动注册 ToolCallingAdvisor，循环它管
ChatClient.create(chatModel)
    .prompt(question)
    .tools(new MyTools())
    .call().content();

// 真要底层控制：自己用 ToolCallingManager 驱动循环
```

### 3.2 internalToolExecutionEnabled 选项移除

`ToolCallingChatOptions.internalToolExecutionEnabled` 及对应配置项全部移除（09 章模式③的开关没了）。用户自控循环的新写法：**不挂 ToolCallingAdvisor**，直接调 ChatModel 自己 `hasToolCalls()` 循环，用 `ToolCallingManager` 执行工具。

### 3.3 ChatClient 自动注册 ToolCallingAdvisor

- 有工具就自动挂 ToolCallingAdvisor，不用显式添加（显式加会挂两份！）
- 自定义：构造时传 `ToolCallingAdvisor.Builder`，或关自动注册手动挂
- 新属性 `spring.ai.chat.client.tool-calling.enabled`

### 3.4 命名与 API 清理

- `ToolCallAdvisor` → **`ToolCallingAdvisor`**
- `FunctionCallback` API → **`ToolCallback` API**（旧名移除）
- `SpringBeanToolCallbackResolver` / `toolNames()` 移除：工具必须显式注册为 ToolCallback 或 `@Tool` 对象
- 工具解析 fallback 默认关闭；新增 Tool Call Limits

### 3.5 新能力：Tool Search（工具太多时的救星）

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-tool-search-advisor</artifactId>
</dependency>
```

```yaml
spring.ai.chat.client.tool-search-advisor.enabled=true
spring.ai.chat.client.tool-search-advisor.tool-index-type=regex   # 或 lucene / vector
```

替换默认 ToolCallingAdvisor，每次只把**最相关的工具定义**发给 LLM（关键词/语义搜索），解决"工具几百个把 prompt 撑爆"的问题。

### 3.6 工具循环历史不再进 ToolContext

ToolCallingAdvisor 内部管理工具循环中的对话历史；**记忆 Advisor 只存最终的 user/assistant 往返**，不写 tool 消息进 ChatMemory（配合记忆顺序调整：`DEFAULT_CHAT_MEMORY_PRECEDENCE_ORDER` 从 +1000 改 +200）。

## 4. Chat Memory 收紧

| 变化 | 影响 |
|------|------|
| **Conversation ID 强制必填** | 缺失/null 直接抛 IllegalArgumentException（我们一直强调的"每次必传"升级为硬约束） |
| `ChatMemory.DEFAULT_CONVERSATION_ID` 移除 | 不能再偷懒用 "default" |
| 记忆 Advisor 的 `.conversationId()` builder 移除 | 只能调用时经 advisor context 传 |
| `PromptChatMemoryAdvisor` 移除 | 1.1.3 废弃的兑现，全用 MessageChatMemoryAdvisor |
| JDBC 记忆表加 `sequence_id` 列 | 迁移脚本要改 |
| Redis 记忆模块改名（2.0.1） | 依赖坐标变了 |

## 5. Options 严格不可变

- `copy()` / `fromOptions()` 移除 → 用 `mutate().xxx().build()`
- 集合返回不可修改；默认值收进 Options 构造器
- `N()` 改名 `n()`；配置属性扁平化

## 6. MCP 大迁移（对 12–14 章的影响）

- 注解并入 Spring AI：`org.springaicommunity.mcp.*` → `org.springframework.ai.mcp.annotation.*`（可 OpenRewrite 自动迁移）
- MCP Spring 传输模块移入 Spring AI，Maven groupId 变了
- MCP SDK 2.0：`Tool.inputSchema` 从 JsonSchema 变 `Map<String,Object>`；**服务端工具入参校验默认开启**；elicitation 用 `ParameterizedTypeReference`（和 05 章泛型擦除对策一致）
- 2.0.1：`@McpTool` 异常处理对齐 `@Tool`

## 7. 模块移除

`spring-ai-azure-openai`、`spring-ai-openai-sdk`、`spring-ai-oci-genai`、hanadb-store 模块删除（OpenAI Java SDK 迁移线）。

## 8. 其他值得一提

- **默认 temperature 配置移除**：各提供商默认值行为变化，显式设置
- OpenAI 工具调用 strict mode 默认改 false
- JSON 工具重构：`JsonHelper` 新增、`JsonParser` 废弃、`ModelOptionsUtils` 的 JSON 方法移除
- BeanOutputConverter 的 JSON Schema 生成变化
- 可观测性：工具调用观测调整（呼应 16 章）

## 9. 对学习路线的影响

```text
现在（1.1.x）：概念全学、按 1.1 API 写 —— 概念 100% 有效
升级时：对着 upgrade-notes 过一遍，重点三条
  ① 工具循环归属（ChatModel → ToolCallingAdvisor）
  ② conversationId 强制
  ③ Options mutate() 化 + MCP 包名
最省力的自查：OpenRewrite 迁移脚本（MCP 包名/依赖）+ 编译器找 copy()/internalToolExecutionEnabled
```
