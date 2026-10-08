# 13 MCP Client Boot Starter

> 来源：Spring AI 官方文档 `api/mcp/mcp-client-boot-starter-docs.html`（1.1.x）。前置：第 12 章 MCP 开篇。

## 学习目标

- 会选 Client Starter（标准 vs WebFlux）
- 掌握三种传输（STDIO / Streamable-HTTP / SSE）的连接配置
- 避开 Windows STDIO 与 SSE URL 拆分两个坑
- 会用四大扩展点：Customizer、ToolFilter、名称前缀、ToolContext→Meta

## 1. 核心心智模型

```text
MCP Client Boot Starter = 自动配置一堆 McpSyncClient / McpAsyncClient
一个连接（connection）= 一个 MCP 客户端实例 = 对一个 MCP Server 的会话
工具自动汇成 ToolCallbackProvider → 进 ChatClient（与 09 章本地工具同路）
```

Starter 提供：多客户端管理、自动初始化、多命名传输、工具框架集成、工具过滤、名称前缀、生命周期清理、Customizer 定制。

## 2. 两个 Starter

```xml
<!-- 标准：STDIO + SSE + Streamable-HTTP + Stateless（JDK HttpClient 实现） -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-client</artifactId>
</dependency>

<!-- WebFlux：Streamable-HTTP + Stateless + SSE（WebFlux 实现） -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-client-webflux</artifactId>
</dependency>
```

- 每个连接创建一个客户端实例；SYNC/ASYNC 全局统一、不可混
- **生产推荐 WebFlux 版**（reactive 传输更适合生产部署）

## 3. 通用属性（`spring.ai.mcp.client`）

| 属性 | 说明 | 默认 |
|------|------|------|
| enabled | 开关 | true |
| name / version | 客户端标识 | spring-ai-mcp-client / 1.0.0 |
| initialized | 创建即初始化 | true |
| request-timeout | 请求超时 | 20s |
| type | SYNC / ASYNC（不可混） | SYNC |
| root-change-notification | roots 变更通知 | true |
| toolcallback.enabled | 工具回调集成 | true |

## 4. 三种传输配置（全部示例）

### 4.1 STDIO

```yaml
spring:
  ai:
    mcp:
      client:
        stdio:
          root-change-notification: true
          connections:
            server1:
              command: /path/to/server
              args:
                - --port=8080
                - --mode=production
              env:
                API_KEY: your-api-key
                DEBUG: "true"
```

或用 Claude Desktop 格式外部 JSON：

```yaml
spring:
  ai:
    mcp:
      client:
        stdio:
          servers-configuration: classpath:mcp-servers.json
```

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
               "/Users/username/Desktop", "/Users/username/Downloads"]
    }
  }
}
```

### 4.2 Windows STDIO 坑

npx/npm/python/pip/mvn/gradle 都是 .cmd 批处理，Java ProcessBuilder 跑不了，要 `cmd.exe /c` 包装：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-filesystem",
               "C:\\Users\\username\\Desktop"]
    }
  }
}
```

跨平台程序化配置（检测 OS 自建 Bean）：

```java
@Bean(destroyMethod = "close")
@ConditionalOnMissingBean(McpSyncClient.class)
public McpSyncClient mcpClient() {
    ServerParameters stdioParams;
    if (isWindows()) {
        var winArgs = new ArrayList<>(Arrays.asList(
            "/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "target"));
        stdioParams = ServerParameters.builder("cmd.exe").args(winArgs).build();
    } else {
        stdioParams = ServerParameters.builder("npx")
                .args("-y", "@modelcontextprotocol/server-filesystem", "target")
                .build();
    }
    return McpClient.sync(new StdioClientTransport(stdioParams, McpJsonMapper.createDefault()))
            .requestTimeout(Duration.ofSeconds(10))
            .build()
            .initialize();
}
```

路径建议用相对路径（按应用工作目录解析，可移植）；Windows 绝对路径用反斜杠。

### 4.3 Streamable-HTTP

```yaml
spring:
  ai:
    mcp:
      client:
        streamable-http:
          connections:
            server1:
              url: http://localhost:8080
            server2:
              url: http://otherserver:8081
              endpoint: /custom-sse    # 默认 /mcp
```

### 4.4 SSE

```yaml
spring:
  ai:
    mcp:
      client:
        sse:
          connections:
            server1:
              url: http://localhost:8080          # 默认端点 /sse
            server2:
              url: http://otherserver:8081
              sse-endpoint: /custom-sse
            mcp-hub:
              url: http://localhost:3000
              sse-endpoint: /mcp-hub/sse/cf9ec4527e3c4a2cbb149a85ea45ab01
            api-server:
              url: https://api.example.com
              sse-endpoint: /v1/mcp/events?token=abc123&format=json
```

**URL 拆分规则**：`url` 只放 scheme+host+port；路径+查询串放 `sse-endpoint`：

| 完整 URL | url | sse-endpoint |
|---------|-----|--------------|
| http://localhost:3000/mcp-hub/sse/token123 | localhost:3000 | /mcp-hub/sse/token123 |
| https://api.service.com/v2/events?key=secret | api.service.com | /v2/events?key=secret |

**排障**：404 先查 URL 拆分；endpoint 要以 `/` 开头；用浏览器/curl 直接验完整 URL。

## 5. Usage Example（完整装配）

```yaml
spring:
  ai:
    mcp:
      client:
        enabled: true
        name: my-mcp-client
        version: 1.0.0
        request-timeout: 30s
        type: SYNC  # 或 ASYNC
        sse:
          connections:
            server1: { url: http://localhost:8080 }
        streamable-http:
          connections:
            server3: { url: http://localhost:8083, endpoint: /mcp }
        stdio:
          connections:
            server1:
              command: /path/to/server
              args: [--port=8080, --mode=production]
```

```java
@Autowired
private List<McpSyncClient> mcpSyncClients;          // 或 McpAsyncClient

@Autowired
private SyncMcpToolCallbackProvider toolCallbackProvider;
ToolCallback[] toolCallbacks = toolCallbackProvider.getToolCallbacks();

// 经典用法：直接挂进 ChatClient（见第 12 章示例 B）
chatClient.prompt("...").toolCallbacks(mcpTools).call().content();
```

## 6. Sync/Async 与传输支持

- `type=SYNC`（默认）/ `ASYNC`；**全应用统一，不能混**
- SYNC 只注册同步注解方法、ASYNC 只注册异步注解方法
- 传输：STDIO（两个 starter 都有）；HttpClient 版 HTTP/SSE、Streamable-HTTP（标准 starter）；WebFlux 版（webflux starter）

## 7. 四大扩展点（全部示例）

### 7.1 Client Customizer

```java
@Component
public class CustomMcpSyncClientCustomizer implements McpSyncClientCustomizer {
    @Override
    public void customize(String serverConfigurationName, McpClient.SyncSpec spec) {
        spec.requestTimeout(Duration.ofSeconds(30));
        spec.roots(roots);                          // 文件系统边界
        spec.sampling((CreateMessageRequest r) -> { // 服务器反向请求 LLM
            return ...;                             // 客户端掌控模型访问权
        });
        spec.elicitation((ElicitRequest request) -> // 服务器向用户要信息
            new ElicitResult(ElicitResult.Action.ACCEPT, Map.of("message", request.message())));
        spec.progressConsumer(p -> { });            // 长任务进度
        spec.toolsChangeConsumer(tools -> { });     // 工具列表变更
        spec.resourcesChangeConsumer(r -> { });
        spec.promptsChangeConsumer(p -> { });
        spec.loggingConsumer(log -> { });
    }
}
```

`serverConfigurationName` 就是连接名；自动检测所有 Customizer Bean 并应用。异步侧实现 `McpAsyncClientCustomizer`。

### 7.2 Tool Filtering

```java
@Component
public class CustomMcpToolFilter implements McpToolFilter {
    @Override
    public boolean test(McpConnectionInfo connectionInfo, McpSchema.Tool tool) {
        if (connectionInfo.clientInfo().name().equals("restricted-client")) return false;
        if (tool.name().startsWith("allowed_")) return true;
        if (tool.description() != null && tool.description().contains("experimental")) return false;
        return true;
    }
}
```

`McpConnectionInfo` = clientCapabilities + clientInfo + initializeResult。**只定义一个** McpToolFilter Bean（要多个就合成一个）。

### 7.3 Tool Name Prefix Generation

默认 `DefaultMcpToolNamePrefixGenerator`：非字母数字转下划线（`my-special-tool` → `my_special_tool`）；跨连接重名加计数前缀（`search` 第二次出现 → `alt_1_search`）；≤64 字符；线程安全幂等。

```java
@Component
public class CustomToolNamePrefixGenerator implements McpToolNamePrefixGenerator {
    @Override
    public String prefixedToolName(McpConnectionInfo connectionInfo, Tool tool) {
        String serverName = connectionInfo.initializeResult().serverInfo().name();
        String serverVersion = connectionInfo.initializeResult().serverInfo().version();
        return serverName + "_v" + serverVersion.replace(".", "_") + "_" + tool.name();
    }
}

// 或者完全不加前缀（多 server 会因重名抛 IllegalStateException，不推荐）
@Bean
public McpToolNamePrefixGenerator mcpToolNamePrefixGenerator() {
    return McpToolNamePrefixGenerator.noPrefix();
}
```

### 7.4 ToolContext → MCP Meta Converter

```java
// 把 ToolContext 里的 progressToken 传给 MCP Progress 流
String response = ChatClient.create(chatModel)
        .prompt("Tell me more about the customer with ID 42")
        .toolContext(Map.of("progressToken", "my-progress-token"))
        .call()
        .content();
```

默认 `defaultConverter()`：过滤掉 MCP exchange key 和 null 值，其余原样进 metadata。自定义：

```java
@Component
public class CustomToolContextToMcpMetaConverter implements ToolContextToMcpMetaConverter {
    @Override
    public Map<String, Object> convert(ToolContext toolContext) {
        Map<String, Object> metadata = new HashMap<>();
        for (Map.Entry<String, Object> entry : toolContext.getContext().entrySet()) {
            if (entry.getValue() != null) {
                metadata.put("app_" + entry.getKey(), entry.getValue());
            }
        }
        metadata.put("timestamp", System.currentTimeMillis());
        return metadata;
    }
}

// 彻底关掉：
@Bean
public ToolContextToMcpMetaConverter toolContextToMcpMetaConverter() {
    return ToolContextToMcpMetaConverter.noOp();
}
```

## 8. MCP Client 注解（本页清单）

`@McpLogging`、`@McpSampling`、`@McpElicitation`、`@McpProgress`、`@McpToolListChanged`、`@McpResourceListChanged`、`@McpPromptListChanged`——细节在 annotations-client 页（第 12 章有速览）。

关闭工具集成：`spring.ai.mcp.client.toolcallback.enabled=false`（不再生成 ToolCallbackProvider）。

## 9. 与前文串联

- `SyncMcpToolCallbackProvider.getToolCallbacks()` = 09 章的 ToolCallback[]，进 ChatClient 后模型无差别
- ToolContext→Meta 是 09 章 ToolContext 多租户思路在 MCP 上的延伸
- 生产传输选型见第 12 章；安全（OAuth2）在 mcp-security 页

## 10. 生产边界

- 生产推荐 `spring-ai-starter-mcp-client-webflux`
- 多 server 环境保留默认前缀生成器
- Windows 部署 cmd.exe 包装；路径用相对路径
- SSE 排障先查 URL 拆分
- ToolFilter 收敛暴露面；只放一个 Filter Bean
- 超时（request-timeout，默认 20s）按对端工具耗时调
