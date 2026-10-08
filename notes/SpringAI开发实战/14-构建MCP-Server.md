# 14 构建 MCP Server

> 来源：Spring AI 官方文档 `api/mcp/mcp-server-boot-starter-docs.html` + `api/mcp/mcp-annotations-server.html` + getting-started 指南（1.1.x）。前置：第 12、13 章。

## 学习目标

- 掌握构建 MCP Server 的五步法
- 会写 @McpTool / @McpResource / @McpPrompt / @McpComplete 四类方法
- 理解 Sync/Async × Stateful/Stateless 的方法过滤矩阵（防"方法没注册"的坑）
- 会用请求上下文、进度上报、动态 Schema 等进阶能力

## 1. 核心心智模型

```text
构建 MCP Server = 引 starter + 写 @McpXxx 注解方法 + 选协议 + 启动
自动配置扫描注解 Bean → 生成规格 → 注册到 McpServer —— 零注册代码
对 Client 来说你的 Spring Boot 应用就是一个标准 MCP Server
```

## 2. 五步构建法

### 第 1 步：选协议、引依赖

| 服务类型 | 依赖 | 属性 |
|---------|------|------|
| STDIO | `spring-ai-starter-mcp-server` | `spring.ai.mcp.server.stdio=true` |
| WebMVC（SSE/STREAMABLE/STATELESS） | `spring-ai-starter-mcp-server-webmvc` | `spring.ai.mcp.server.protocol=SSE`（或空）/ `STREAMABLE` / `STATELESS` |
| WebFlux 三种 | `spring-ai-starter-mcp-server-webflux` | 同上 |

新项目选 Streamable-HTTP；Stateless 适合微服务/云原生（无会话）。

### 第 2 步：写工具（@McpTool）

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

### 第 3 步：（可选）写资源和提示词

见第 4 节示例。

### 第 4 步：配置

```yaml
spring:
  ai:
    mcp:
      server:
        protocol: STREAMABLE
        type: SYNC            # 或 ASYNC
        annotation-scanner:
          enabled: true       # 默认开
```

### 第 5 步：启动验证

`@SpringBootApplication` 原样启动即可，自动配置完成扫描注册。用第 13 章的 client 连上测。

## 3. Server 能力清单

Tools、Resources、Prompts、Completions、Logging、Progress、Ping——默认全开，可禁用（禁用即不注册不暴露）。

## 4. 四类注解（全部示例）

### 4.1 @McpTool —— 工具

基础：

```java
@McpTool(name = "add", description = "Add two numbers together")
public int add(
        @McpToolParam(description = "First number", required = true) int a,
        @McpToolParam(description = "Second number", required = true) int b) {
    return a + b;
}
```

进阶（注解元数据 hints——告诉模型这工具是否只读/幂等）：

```java
@McpTool(name = "calculate-area",
         description = "Calculate the area of a rectangle",
         annotations = McpTool.McpAnnotations(
             title = "Rectangle Area Calculator",
             readOnlyHint = true,
             destructiveHint = false,
             idempotentHint = true
         ))
public AreaResult calculateRectangleArea(
        @McpToolParam(description = "Width", required = true) double width,
        @McpToolParam(description = "Height", required = true) double height) {
    return new AreaResult(width * height, "square units");
}
```

请求上下文（日志/进度/ping）：

```java
@McpTool(name = "process-data", description = "Process data with request context")
public String processData(
        McpSyncRequestContext context,
        @McpToolParam(description = "Data to process", required = true) String data) {
    context.info("Processing data: " + data);
    context.progress(p -> p.progress(0.5).total(1.0).message("Processing..."));
    context.ping();
    return "Processed: " + data.toUpperCase();
}
```

动态 Schema（运行时接收任意参数）：

```java
@McpTool(name = "flexible-tool", description = "Process dynamic schema")
public CallToolResult processDynamic(CallToolRequest request) {
    Map<String, Object> args = request.arguments();
    String result = "Processed " + args.size() + " arguments dynamically";
    return CallToolResult.builder().addTextContent(result).build();
}
```

进度跟踪（长任务）：

```java
@McpTool(name = "long-task", description = "Long-running task with progress")
public String performLongTask(
        McpSyncRequestContext context,
        @McpToolParam(description = "Task name", required = true) String taskName) {
    String progressToken = context.request().progressToken();
    if (progressToken != null) {
        context.progress(p -> p.progress(0.0).total(1.0).message("Starting task"));
        // ... 干活 ...
        context.progress(p -> p.progress(1.0).total(1.0).message("Task completed"));
    }
    return "Task " + taskName + " completed";
}
```

### 4.2 @McpResource —— URI 资源

```java
@McpResource(uri = "config://{key}", name = "Configuration",
             description = "Provides configuration data")
public String getConfig(String key) {
    return configData.get(key);
}

// 返回结构化结果
@McpResource(uri = "user-profile://{username}", name = "User Profile")
public ReadResourceResult getUserProfile(String username) {
    String profileData = loadUserProfile(username);
    return new ReadResourceResult(List.of(
        new TextResourceContents("user-profile://" + username, "application/json", profileData)
    ));
}

// 带上下文
@McpResource(uri = "data://{id}", name = "Data Resource")
public ReadResourceResult getData(McpSyncRequestContext context, String id) {
    context.info("Accessing resource: " + id);
    context.ping();
    return new ReadResourceResult(List.of(
        new TextResourceContents("data://" + id, "text/plain", fetchData(id))
    ));
}
```

### 4.3 @McpPrompt —— 提示词模板

```java
@McpPrompt(name = "greeting", description = "Generate a greeting message")
public GetPromptResult greeting(
        @McpArg(name = "name", description = "User's name", required = true) String name) {
    String message = "Hello, " + name + "! How can I help you today?";
    return new GetPromptResult("Greeting",
        List.of(new PromptMessage(Role.ASSISTANT, new TextContent(message))));
}

// 可选参数
@McpPrompt(name = "personalized-message", description = "Generate a personalized message")
public GetPromptResult personalizedMessage(
        @McpArg(name = "name", required = true) String name,
        @McpArg(name = "age", required = false) Integer age,
        @McpArg(name = "interests", required = false) String interests) {
    // 按可选参数拼内容
    ...
}
```

### 4.4 @McpComplete —— 自动补全

```java
@McpComplete(prompt = "city-search")
public List<String> completeCityName(String prefix) {
    return cities.stream()
        .filter(city -> city.toLowerCase().startsWith(prefix.toLowerCase()))
        .limit(10).toList();
}

// 按参数名区分补全
@McpComplete(prompt = "travel-planner")
public List<String> completeTravelDestination(CompleteRequest.CompleteArgument argument) {
    String prefix = argument.value().toLowerCase();
    if ("city".equals(argument.name())) return completeCities(prefix);
    if ("country".equals(argument.name())) return completeCountries(prefix);
    return List.of();
}

// 返回 CompleteResult（total / hasMore）
@McpComplete(prompt = "code-completion")
public CompleteResult completeCode(String prefix) {
    List<String> completions = generateCodeCompletions(prefix);
    return new CompleteResult(new CompleteResult.CompleteCompletion(
        completions, completions.size(), hasMoreCompletions));
}
```

## 5. 上下文三档（按需选）

| 档位 | 参数类型 | 能力 | 适用 |
|------|---------|------|------|
| 统一上下文（推荐） | `McpSyncRequestContext` / `McpAsyncRequestContext` | request/元数据 + info/progress/ping + elicit/sample（仅 Stateful） | 有状态双向 |
| 无上下文 | 不加参数 | 纯入参出参 | 简单操作 |
| 轻量无状态 | `McpTransportContext` | 传输级上下文 | Stateless 部署 |

统一上下文示例（能力开关先判断再用）：

```java
@McpTool(name = "unified-tool", description = "Tool with unified request context")
public String unifiedTool(
        McpSyncRequestContext context,
        @McpToolParam(description = "Input", required = true) String input) {
    context.info("Processing: " + input);
    context.progress(50);                 // 简单百分比
    context.ping();
    if (context.elicitEnabled()) {        // 仅 Stateful：向用户要信息
        StructuredElicitResult<UserInfo> r = context.elicit(UserInfo.class);
    }
    if (context.sampleEnabled()) {        // 仅 Stateful：反向请求 LLM
        CreateMessageResult s = context.sample("Generate response");
    }
    return "Processed with unified context";
}
```

⚠️ Stateless 服务器**不支持双向操作**：带 `McpSyncRequestContext` 的方法会被忽略（只接受 `McpTransportContext` 或无上下文）。

## 6. 方法过滤矩阵（大坑预警）

框架按服务器类型自动过滤注解方法，被过滤的会打 WARN 日志：

| 服务器类型 | 接受 | 过滤掉 |
|-----------|------|--------|
| Sync Stateful | 非响应式返回值 + 双向上下文 | Mono/Flux 返回 |
| Async Stateful | Mono/Flux 返回 + 双向上下文 | 非响应式返回 |
| Sync Stateless | 非响应式 + 无双向上下文 | 响应式返回 **或** 双向上下文参数 |
| Async Stateless | 响应式 + 无双向上下文 | 非响应式 **或** 双向上下文参数 |

最佳实践：方法风格与服务器类型对齐；Stateful/Stateless 实现分不同类；启动看 WARN 日志；要支持两种部署就两种都测。

## 7. 异步支持（Reactor）

```java
@McpTool(name = "async-fetch", description = "Fetch data asynchronously")
public Mono<String> asyncFetch(
        @McpToolParam(description = "URL", required = true) String url) {
    return Mono.fromCallable(() -> fetchFromUrl(url))
            .subscribeOn(Schedulers.boundedElastic());
}

@McpResource(uri = "async-data://{id}", name = "Async Data")
public Mono<ReadResourceResult> asyncResource(String id) {
    return Mono.fromCallable(() -> new ReadResourceResult(List.of(
        new TextResourceContents("async-data://" + id, "text/plain", loadData(id))
    ))).delayElements(Duration.ofMillis(100));
}
```

## 8. 自动配置做了什么

启动时：扫描带 MCP 注解的 Bean → 生成规格 → 注册到 MCP Server → 按 `type` 处理 sync/async。业务代码零注册逻辑。

## 9. 与前文串联

- Server 暴露的工具在 Client 侧变成 `ToolCallback`（12/13 章），进 ChatClient 后与 09 章 `@Tool` 本地工具对模型无差别
- `@McpTool` vs `@Tool`：前者走 MCP 协议跨进程，后者进程内直调；描述写法要求一致（都是给模型看的 prompt）
- 进度/日志/双向能力对应 Client 侧 Customizer 的 progressConsumer/loggingConsumer/sampling（13 章）

## 10. 生产边界

- 新项目协议选 STREAMABLE；写操作工具加 `destructiveHint = true` 等 hints 帮模型避雷
- description / @McpToolParam description 认真写——就是模型的决策依据
- 长任务必接进度上报（progressToken）
- 启动日志检查"filtered method"警告，防方法悄悄没注册
- 对外暴露的 Server 记得配安全（mcp-security 页，OAuth2 等）
