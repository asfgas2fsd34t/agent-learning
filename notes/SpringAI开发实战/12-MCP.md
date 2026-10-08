# 12 MCP（Model Context Protocol）

> 来源：Spring AI 官方文档 `api/mcp/` 章节（mcp-overview、getting-started-mcp、mcp-client-boot-starter、mcp-server-boot-starter、mcp-annotations-overview，1.1.x）。

## 学习目标

- 理解 MCP 是什么：AI 与外部工具/资源的标准协议
- 掌握 MCP Java SDK 三层架构与 Client/Server 职责划分
- 会选 Starter 和协议（STDIO / SSE / Streamable-HTTP / Stateless）
- 跑通 Quick Start：@McpTool 写 Server、ChatClient 消费
- 了解 MCP 注解体系与 Client 实用特性（过滤、前缀、Meta 转换）

## 1. 核心心智模型

```text
MCP = AI 模型 ↔ 外部工具/资源 的标准化协议（类比 USB-C）
底层是 JSON-RPC 消息；传输支持 STDIO、HTTP/SSE、Streamable-HTTP 等
Spring AI 的位置：MCP Java SDK（Spring 团队开发维护）之上
  → Boot Starter（自动配置）+ MCP Annotations（声明式）
  → Spring 应用既能当 Client 消费别人的 MCP Server，
    也能当 Server 把自己的服务暴露给整个 AI 生态
```

## 2. MCP Java SDK 三层架构

| 层 | 组件 | 职责 |
|----|------|------|
| Client/Server 层 | McpClient / McpServer | 协议操作、业务逻辑 |
| Session 层 | McpSession（McpClientSession / McpServerSession） | 会话与连接状态 |
| Transport 层 | McpTransport | JSON-RPC 序列化；STDIO / HTTP-SSE / Streamable-HTTP |

- **McpClient**：协议/能力协商、消息传输、工具发现执行、资源访问、Prompt 交互；可选 Roots、Sampling
- **McpServer**：工具暴露、资源（URI）、Prompt 模板、能力协商、结构化日志、并发客户端管理

## 3. Starter 与协议速查

### 客户端

| Starter | 传输 |
|---------|------|
| `spring-ai-starter-mcp-client` | STDIO、Servlet Streamable-HTTP、Stateless、SSE |
| `spring-ai-starter-mcp-client-webflux` | WebFlux Streamable-HTTP、Stateless、SSE |

### 服务端

| 服务类型 | 依赖 | 属性 |
|---------|------|------|
| STDIO | `spring-ai-starter-mcp-server` | `spring.ai.mcp.server.stdio=true` |
| SSE WebMVC | `spring-ai-starter-mcp-server-webmvc` | `spring.ai.mcp.server.protocol=SSE` 或空 |
| Streamable-HTTP WebMVC | 同上 | `protocol=STREAMABLE` |
| Stateless WebMVC | 同上 | `protocol=STATELESS` |
| WebFlux 三种 | `spring-ai-starter-mcp-server-webflux` | 同上对应值 |

### 协议怎么选

- **STDIO**：进程/子进程内通信（本地工具）
- **SSE**：独立服务多客户端（旧，被 Streamable-HTTP 取代）
- **Streamable-HTTP**：HTTP POST/GET + 可选 SSE 流，新项目默认选它
- **Stateless**：无会话状态，微服务/云原生部署

## 4. Quick Start（全部示例）

### Server：@McpTool 暴露工具

```java
@Service
public class WeatherService {

    @McpTool(description = "Get current temperature for a location")
    public String getTemperature(
            @McpToolParam(description = "City name", required = true) String city) {
        return String.format("Current temperature in %s: 22°C", city);
    }
}
```

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

```properties
spring.ai.mcp.server.protocol=STREAMABLE
```

### Client：ChatClient 消费 MCP 工具

```java
@Bean
public CommandLineRunner demo(ChatClient chatClient, ToolCallbackProvider mcpTools) {
    return args -> {
        String response = chatClient
            .prompt("What's the weather like in Paris?")
            .toolCallbacks(mcpTools)
            .call()
            .content();
        System.out.println(response);
    };
}
```

```yaml
spring:
  ai:
    mcp:
      client:
        streamable-http:
          connections:
            weather-server:
              url: http://localhost:8080
```

## 5. Server 能力与 Sync/Async

能力（默认全开，可禁用）：Tools、Resources、Prompts、Completions、Logging、Progress、Ping。

```text
spring.ai.mcp.server.type=SYNC（默认，McpSyncServer）| ASYNC（McpAsyncServer）
SYNC 只注册同步注解方法；ASYNC 只注册异步注解方法 —— 两边互不注册，别混写
Client 同理：spring.ai.mcp.client.type=SYNC|ASYNC（不允许混用）
```

## 6. MCP 注解体系

| 侧 | 注解 | 作用 |
|----|------|------|
| Server | `@McpTool` / `@McpResource` / `@McpPrompt` / `@McpComplete` | 工具、资源 URI 模板、提示词模板、自动补全 |
| Client | `@McpLogging` / `@McpSampling` / `@McpElicitation` / `@McpProgress` / `@McpToolListChanged` / `@McpResourceListChanged` / `@McpPromptListChanged` | 通知与请求的声明式处理 |

特殊参数（自动注入、不进 JSON Schema）：`McpSyncRequestContext`/`McpAsyncRequestContext`（统一上下文）、`McpTransportContext`（无状态轻量）、`@McpProgressToken`、`McpMeta`、`CallToolRequest`。

```java
@Component
public class CalculatorTools {

    @McpTool(name = "add", description = "Add two numbers together")
    public int add(
            @McpToolParam(description = "First number", required = true) int a,
            @McpToolParam(description = "Second number", required = true) int b) {
        return a + b;
    }

    @McpResource(uri = "config://{key}", name = "Configuration")
    public String getConfig(String key) {
        return configData.get(key);
    }
}
```

```java
@Component
public class LoggingHandler {

    @McpLogging(clients = "my-server")
    public void handleLoggingMessage(LoggingMessageNotification notification) {
        System.out.println("Received log: " + notification.level() + " - " + notification.data());
    }
}
```

扫描配置（starter 默认开启）：

```yaml
spring:
  ai:
    mcp:
      client:
        annotation-scanner:
          enabled: true
      server:
        annotation-scanner:
          enabled: true
```

## 7. Client 配置速查

### 通用属性（`spring.ai.mcp.client`）

| 属性 | 说明 | 默认 |
|------|------|------|
| enabled | 开关 | true |
| name / version | 客户端标识 | spring-ai-mcp-client / 1.0.0 |
| request-timeout | 请求超时 | 20s |
| type | SYNC / ASYNC | SYNC |
| toolcallback.enabled | 工具回调集成 | true |

### 三种传输连接配置

```yaml
spring:
  ai:
    mcp:
      client:
        stdio:
          connections:
            server1:
              command: /path/to/server
              args: [--port=8080, --mode=production]
              env:
                API_KEY: your-api-key
          # 或用 Claude Desktop 格式外部 JSON：
          # servers-configuration: classpath:mcp-servers.json
        streamable-http:
          connections:
            server1:
              url: http://localhost:8080
            server2:
              url: http://otherserver:8081
              endpoint: /custom-sse    # 默认 /mcp
        sse:
          connections:
            server1:
              url: http://localhost:8080
            api-server:
              url: https://api.example.com
              sse-endpoint: /v1/mcp/events?token=abc123   # 默认 /sse
```

Claude Desktop 格式（`mcp-servers.json`）：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/username/Desktop"]
    }
  }
}
```

### Windows STDIO 坑

npx/npm/python 等是 .cmd 批处理，Java ProcessBuilder 执行不了，要 `cmd.exe /c` 包装：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\username\\Desktop"]
    }
  }
}
```

跨平台方案：程序里检测 OS 自建 `McpSyncClient` Bean（记得 `@ConditionalOnMissingBean(McpSyncClient.class)` 防和自动配置打架）。

### 注入使用

```java
@Autowired
private List<McpSyncClient> mcpSyncClients;          // 或 McpAsyncClient

@Autowired
private SyncMcpToolCallbackProvider toolCallbackProvider;
ToolCallback[] toolCallbacks = toolCallbackProvider.getToolCallbacks();
```

## 8. Client 实用特性

| 特性 | 扩展点 | 作用 |
|------|--------|------|
| 客户端定制 | `McpSyncClientCustomizer` / `McpAsyncClientCustomizer` | 超时、roots、sampling、elicitation、事件回调 |
| 工具过滤 | `McpToolFilter`（只定义一个 Bean） | 按连接/工具属性收敛暴露面 |
| 工具名前缀 | `McpToolNamePrefixGenerator` | 多 server 工具重名去重（默认 `alt_1_xxx`；`noPrefix()` 可关但多 server 会炸） |
| ToolContext→Meta | `ToolContextToMcpMetaConverter` | 把 ToolContext（userId、progressToken）转成 MCP 调用元数据 |
| 关闭工具集成 | `spring.ai.mcp.client.toolcallback.enabled=false` | 不生成 ToolCallbackProvider |

## 9. 与前文串联

| | 本地工具（09 章 @Tool） | MCP 工具 |
|--|------------------------|----------|
| 位置 | 你的应用进程内方法 | 另一个进程/机器，经标准协议暴露 |
| 定义 | `@Tool` / FunctionToolCallback | 对端 `@McpTool`，本端配置连接 |
| 进入模型 | ToolCallback | 同样是 ToolCallback（SyncMcpToolCallbackProvider） |
| 模型视角 | tool_calls，无差别 | 同左 |
| 治理 | 你的代码，随便改 | 第三方能力边界，要过滤/鉴权（09 的 ToolContext 思路同样适用） |

一句话：**MCP 是把 09 章的工具从"进程内"推到"跨进程/跨团队"的标准协议**，进 ChatClient 后模型根本分不出来。

## 10. 本章其余页面（后续可读）

- `mcp-annotations-client/server/special-params/examples`：注解四页细化
- `mcp-security`：安全（OAuth2 等）
- `mcp-stdio-sse-server / mcp-streamable-http-server / mcp-stateless-server`：传输变体 starter 细节

## 11. 生产边界

- 新项目协议选 Streamable-HTTP；Stateless 适合云原生
- 多 MCP server 一定要保留默认前缀生成器，防工具重名
- Windows 部署记得 cmd.exe 包装
- 暴露的工具收敛权限（ToolFilter + 对端鉴权）；`@McpTool` 描述就是给模型看的 prompt
- 同步/异步别混：整个应用统一 type
