# 01 ChatClient 流式 API

> 来源：Spring AI 官方文档 `api/chatclient.html`（1.1.x）。

## 学习目标

- 理解 ChatClient 是 Spring AI 的一站式门面（fluent API）
- 掌握 prompt → 内容 → call/stream → 取结果的四段式链式调用
- 分清 `call()` 与 `stream()`、`content()` 与 `entity()` 的选择
- 理解默认配置（defaultSystem / defaultOptions 等）的作用

## 1. 核心心智模型

```text
ChatClient = ChatModel 的流式门面
四段式：prompt() 设置 → 内容选择 → call()/stream() 执行方式 → 取结果
关键：call()/stream() 本身不真正触发模型调用，取结果（content()/entity()...）才触发
```

ChatModel 是底层单次调用 API；ChatClient 在其上叠加了 fluent 链、Advisor 管线、结构化输出、默认配置。日常业务代码优先用 ChatClient。

## 2. 创建方式

```java
// 快捷创建
ChatClient chatClient = ChatClient.create(chatModel);

// 带默认配置创建（推荐生产用）
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultSystem("你是一个简洁的中文助手")
    .defaultOptions(OpenAiChatOptions.builder().temperature(0.3).build())
    .defaultAdvisors(new MessageChatMemoryAdvisor(chatMemory))
    .build();
```

## 3. 四段式链式调用

### 3.1 同步 call

```java
String answer = chatClient.prompt()
    .user("给我讲个笑话")
    .call()
    .content();                      // 取纯文本
```

### 3.2 流式 stream

```java
Flux<String> tokens = chatClient.prompt()
    .user("给我讲个笑话")
    .stream()
    .content();                      // 逐片文本
```

### 3.3 取完整响应 / 结构化结果

```java
ChatResponse response = chatClient.prompt().user("hi").call().chatResponse();

ActorFilms films = chatClient.prompt()
    .user("生成汤姆·汉克斯的电影作品")
    .call()
    .entity(ActorFilms.class);       // 结构化输出（详见 05）

List<ActorFilms> list = chatClient.prompt()
    .user("生成多位演员的作品")
    .call()
    .entity(new ParameterizedTypeReference<List<ActorFilms>>() {});
```

## 4. 设置输入的几种方式

```java
// system + user 分开设置
chatClient.prompt()
    .system("你是客服助手")
    .user("我的订单没收到")
    .call().content();

// 直接给 Prompt 对象（底层 API，详见 04）
chatClient.prompt(new Prompt(List.of(new UserMessage("hi")))).call().content();

// 模板参数
chatClient.prompt()
    .user(u -> u.text("帮我总结这段话：{text}").param("text", article))
    .call().content();
```

## 5. 默认配置 vs 单次配置

| 方法 | 作用范围 | 说明 |
|------|---------|------|
| `defaultSystem()` / `defaultUser()` / `defaultOptions()` / `defaultAdvisors()` | builder 上设置，所有请求生效 | 单次调用仍可覆盖 |
| `system()` / `user()` / `options()` / `advisors()` | 仅本次请求 | 单次设置优先 |

## 6. 示例 11 辨析（两次 stream()）

文档示例 11 里出现了两个 `stream()`，含义完全不同：

```java
chatClient.prompt()
    .user("...")
    .stream()          // ① ChatClient 的流式执行：触发模型流式返回 Flux<ChatResponse>
    .content()
    .map(token -> ...)  // ② Reactor Flux 的 stream 操作 / Java Stream 流式处理
    ...
```

- ① 是 **ChatClient 的流式 API**（`stream()` 相对 `call()`），返回的是响应式流 `Flux`
- ② 是对这个流的**数据处理**（Flux 的 map/filter 等操作符，或 Java `List.stream()`）

一句话：第一个 `stream()` 是"怎么拿模型输出"，第二个是"拿到输出后怎么加工"。

## 7. 与前文串联

- `call()`/`stream()` 取的底层结果是 `ChatResponse`（详见 07 总览：`ChatResponse → generations → Generation → AssistantMessage`）
- 想要 `entity()` 强类型返回，走结构化输出（05）
- 想在链路里加日志/记忆/审核，挂 Advisor（02）
- 对话记忆的 conversationId 通过 `.advisors(a -> a.param(ChatMemory.CONVERSATION_ID, id))` 传入（08）

## 8. 生产边界

- 系统提示词放 `defaultSystem`，业务差异提示词放单次 `system()`/`user()`
- 流式场景（打字机效果）用 `stream()`；后台任务用 `call()`
- `content()` 为 null 时注意兜底（模型拒答或工具循环异常时可能出现）
