# 09 工具调用（Tool Calling）

> 来源：Spring AI 官方文档 `api/tools.html`（1.1.x）。

## 学习目标

- 理解"模型只请求、应用执行"的安全边界
- 掌握三种工具定义方式（@Tool / MethodToolCallback / FunctionToolCallback）
- 理解 ToolContext 与 returnDirect 两大实用特性
- 掌握三种执行模式，特别是用户自控循环
- 了解异常处理与参数增广

## 1. 核心心智模型

```text
模型只生成"我想调用这个工具、参数是这些"的请求（tool_calls）
真正执行的是你的应用代码 —— 这是安全边界（模型碰不到你的系统）
循环：用户提问 → 模型返回 tool_calls → 应用执行 → ToolMessage 回传 → 模型继续 → 直到给出最终回答
```

## 2. Quick Start：@Tool 声明式

```java
public class DateTimeTools {

    @Tool(description = "获取当前日期和时间")
    public String getCurrentDateTime() {
        return LocalDateTime.now().toString();
    }

    @Tool(description = "设置一个闹钟")
    public void setAlarm(@ToolParam(description = "闹钟时间，ISO 格式", required = false)
                         LocalDateTime time) {
        // 设置闹钟逻辑
    }
}

// 挂到 ChatClient
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultTools(new DateTimeTools())     // 或 defaultToolCallbacks(ToolCallbacks.from(new DateTimeTools()))
    .build();

String answer = chatClient.prompt()
    .user("现在几点了？帮我设一个明早 7 点的闹钟")
    .call().content();
```

### @Tool / @ToolParam 要点

- `@Tool(description=...)` 的描述是模型选择工具的依据，写清楚"什么时候用"
- `@ToolParam(required = true)` 是**默认值**：必填参数缺失模型会主动追问而不是瞎编（防幻觉）
- 参数类型用 record/枚举/LDT 等能生成清晰 Schema 的类型

## 3. 三种定义方式

| 方式 | 适用 | 限制 |
|------|------|------|
| `@Tool` 注解方法 | 首选，声明式 | 方法签名需可映射为 JSON Schema |
| `MethodToolCallback` 编程式 | 反射调用既有方法 | 需手工建 ToolDefinition |
| `FunctionToolCallback` + `@Bean` | 逻辑是函数式/要动态开关 | BiFunction\<I, ToolContext, O\>；输入输出类型需简单 |

### 3.1 MethodToolCallback（编程式）

```java
Method method = DateTimeTools.class.getMethod("getCurrentDateTime");
ToolCallback callback = MethodToolCallback.builder()
    .toolDefinition(ToolDefinition.builder()
        .name("getCurrentDateTime")
        .description("获取当前日期和时间")
        .inputSchema("{}")
        .build())
    .toolObject(new DateTimeTools())
    .toolMethod(method)
    .build();
```

### 3.2 FunctionToolCallback（@Bean 动态注册）

```java
@Bean
public ToolCallback weather() {
    return FunctionToolCallback.builder("getWeather", (BiFunction<String, ToolContext, String>) city -> {
        return "晴，25°C";   // 实际调天气 API
    })
    .description("查询城市天气")
    .inputType(String.class)
    .build();
}
```

`@Bean` 注册的工具可以配合 `toolNames` 动态指定本次启用哪些——按场景开关工具，减小 Schema 体积。

## 4. 底层抽象

```java
public interface ToolCallback {
    ToolDefinition getToolDefinition();          // name + description + inputSchema
    String call(String toolInput);               // 执行（旧签名）
    String call(String toolInput, ToolContext ctx);
}
public interface ToolContext {
    Map<String, Object> getContext();            // 不发给模型！应用侧上下文
}
```

`ToolCallResultConverter` 控制工具返回值怎么序列化成 ToolMessage 文本。

## 5. 两大实用特性

### 5.1 ToolContext：不发给模型的私货

```java
public class CustomerTools {
    @Tool(description = "查询当前用户的订单")
    public List<Order> myOrders(ToolContext ctx) {
        String userId = (String) ctx.getContext().get("userId");   // 租户/鉴权信息
        return orderDao.findByUserId(userId);
    }
}

chatClient.prompt()
    .toolContext(Map.of("userId", currentUserId))
    .user("我最近的订单").call().content();
```

多租户、鉴权、traceId 都放这里——**它不会进入模型的 prompt**，模型看不到也伪造不了。

### 5.2 returnDirect：工具结果直接返回

```java
ToolMetadata metadata = ToolMetadata.builder().returnDirect(true).build();
// returnDirect=true 时工具结果不经模型二次加工，直接作为最终回答
```

适合：查询类工具结果本身就是答案（报表、SQL 结果），省一轮 token、防模型转述出错。

## 6. 三种执行模式

| 模式 | 执行方 | 特点 |
|------|--------|------|
| ① 框架托管 | Spring AI 自动 | 默认，while 循环框架写好，业务零感知 |
| ② ToolCallAdvisor | 递归 Advisor | 想在工具循环里挂切面时 |
| ③ 用户自控 | 自己写 while | `internalToolExecutionEnabled=false`，拿 tool_calls 自己执行 |

### 模式③：用户自控循环

```java
// 关闭框架自动执行
OpenAiChatOptions options = OpenAiChatOptions.builder()
    .internalToolExecutionEnabled(false)
    .build();

List<Message> history = new ArrayList<>(List.of(new UserMessage("北京天气如何？")));
Prompt prompt = new Prompt(history, options);

while (true) {
    ChatResponse response = chatModel.call(prompt);
    AssistantMessage output = response.getResult().getOutput();

    if (output.hasToolCalls()) {
        // 把"模型请求调用工具"这条消息记入历史
        history.add(output);
        for (ToolCall toolCall : output.getToolCalls()) {
            String result = myExecute(toolCall);           // 自己执行（可审计、审批、异步）
            history.add(new ToolMessage(toolCall.id(), result));
        }
        prompt = new Prompt(history, options);
    } else {
        history.add(output);                                // 最终回答
        break;
    }
}
```

### 模式③ + ChatMemory 联用

中间轮次（tool_calls 消息、ToolMessage）也要手动存进记忆，否则续聊时上下文断裂：

```java
memory.add(conversationId, List.of(output, toolMessage));
```

## 7. 异常处理

```text
ToolExecutionExceptionProcessor：
- 报错信息回传给模型（RuntimeException）→ 模型自我纠正换参数重试
- 直接抛出（受检异常/未配置）→ 中断调用

spring.ai.tools.throw-exception-on-error=true → 任何工具错误都抛异常，不再回传模型
```

生产建议：可恢复错误（参数格式、网络抖动）回传模型重试；不可恢复（权限、余额不足）直接抛出并给用户友好提示。

## 8. Tool Argument Augmentation（参数增广）

给所有工具的 Schema **追加隐藏字段**（如思考链），模型调用时会填，应用侧消费后在真正执行前剔除：

```java
record AgentThinking(String innerThought) {}

AugmentedToolCallbackProvider<AgentThinking> provider = AugmentedToolCallbackProvider
    .<AgentThinking>builder()
    .toolObject(new MyTools())
    .argumentType(AgentThinking.class)
    .argumentConsumer(event -> {
        AgentThinking thinking = event.arguments();
        log.info("Tool: {} | Reasoning: {}", event.toolDefinition().name(), thinking.innerThought());
    })
    .removeExtraArgumentsAfterProcessing(true)   // true 默认：剔除后调用原工具
    .build();

ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultToolCallbacks(provider)
    .build();
```

用途：强制模型先"想"再调工具（捕获思考链做审计/评测）。

## 9. 可观测性

- `spring.ai.tool` observations 度量耗时、传播 tracing
- 工具入参/结果默认**不**导出为 span 属性（敏感信息保护，可配置开启）
- `org.springframework.ai` 开 DEBUG 看工具选择/执行日志

## 10. 决策速查

| 问题 | 选择 |
|------|------|
| 定义新工具 | `@Tool` 注解 |
| 逻辑是函数/要动态开关 | `@Tool` FunctionToolCallback `@Bean` |
| 需要租户/鉴权上下文 | ToolContext |
| 工具结果即最终答案 | returnDirect |
| 需要审计/审批中间步骤 | 模式③ 自控循环 |
| 一般业务 | 模式① 框架托管 |
| 工具报错要不要让模型重试 | 可恢复→回传；否则→抛出 |

## 11. 生产边界

- 工具描述就是 prompt，写清"何时用、何时不用"
- 工具权限收敛到执行账号本身，别指望模型只调"该调的"
- 写操作工具（下单、发邮件）建议模式③ + 人工确认
- 工具超时要设；慢工具会拖住整个对话
