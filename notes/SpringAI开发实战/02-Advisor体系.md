# 02 Advisor 体系

> 来源：Spring AI 官方文档 `api/advisors.html`（1.1.x）。

## 学习目标

- 理解 Advisor 是请求/响应的栈式拦截器（类似 AOP）
- 分清 Advisor 根接口、BaseAdvisor（自动挡）、CallAdvisor/StreamAdvisor（手工挡）
- 掌握执行顺序（order）语义
- 能写出完整的流式 Advisor 案例

## 1. 核心心智模型

```text
Advisor = Spring AI 调用链上的切面
请求方向：order 小的先执行 before
响应方向：order 小的后执行 after（栈式包裹，先入后出）
Advisor 根接口 = getName() + Ordered，只是"身份"
```

典型用途：对话记忆、日志审计、敏感词过滤、重试、RAG 检索增强、人工审核。

## 2. 三种角色

| 角色 | 接口 | 特点 | 适用 |
|------|------|------|------|
| 根接口 | `Advisor` | 只有 getName + getOrder | 不直接用 |
| 自动挡 | `BaseAdvisor` | 实现 before/after 钩子即可，流式自动适配 | 80% 场景 |
| 手工挡 | `CallAdvisor` / `StreamAdvisor` | 自己控制 chain.next、逐片处理 | 需要精细控制时 |

### 2.1 BaseAdvisor（自动挡）

```java
public abstract class BaseAdvisor implements CallAdvisor, StreamAdvisor {
    // 请求进入时
    protected AdvisedRequest before(AdvisedRequest request) { return request; }
    // 响应完成时（流式只在 finish 时回调一次）
    protected AdvisedResponse after(AdvisedResponse response) { return response; }

    // 自动挡模板：before 改请求 → next 放行 → after 改响应
    @Override
    public AdvisedResponse adviseCall(AdvisedRequest request, CallAdvisorChain chain) {
        AdvisedRequest advisedRequest = before(request);
        AdvisedResponse advisedResponse = chain.next(advisedRequest);
        return after(advisedResponse);
    }
    // adviseStream 同理包装 Flux，after 只在终止信号时执行一次
}
```

要点：**before 改请求、after 改响应、中间放行给下一个**。流式场景下 after 只在流结束（finish reason）时执行一次，不是每个 token 一次。

### 2.2 手工挡 CallAdvisor / StreamAdvisor

```java
public interface CallAdvisor extends Advisor {
    AdvisedResponse adviseCall(AdvisedRequest request, CallAdvisorChain chain);
}
public interface StreamAdvisor extends Advisor {
    Flux<ChatResponse> adviseStream(AdvisedRequest request, StreamAdvisorChain chain);
}
```

手工挡可以：不放行、多次放行（见 03 递归）、逐片改写流内容。

## 3. 完整流式 Advisor 案例：敏感词打码

```java
public class SensitiveWordStreamAdvisor implements StreamAdvisor {

    private static final Pattern SENSITIVE = Pattern.compile("1[3-9]\\d{9}"); // 手机号

    @Override
    public Flux<ChatResponse> adviseStream(AdvisedRequest request, StreamAdvisorChain chain) {
        // 请求侧也可以做改写：request = AdvisedRequest.from(request).build();
        return chain.next(request).map(this::filterChunk);
    }

    private ChatResponse filterChunk(ChatResponse response) {
        Generation gen = response.getResult();
        String text = gen.getOutput().getText();
        if (text == null) return response;
        String masked = SENSITIVE.matcher(text).replaceAll("1**********");
        // 不可变对象：用 builder.from + mutate 改写
        AssistantMessage maskedMsg = new AssistantMessage(masked, gen.getOutput().getMetadata());
        Generation maskedGen = new Generation(maskedMsg, gen.getMetadata());
        return ChatResponse.builder().from(response)
                .generations(List.of(maskedGen))
                .build();
        // 或：response.mutate().generations(...) 方式
    }

    @Override
    public int getOrder() { return Ordered.LOWEST_PRECEDENCE - 100; } // 靠外层

    @Override
    public String getName() { return "SensitiveWordStreamAdvisor"; }
}
```

挂载：

```java
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(new SensitiveWordStreamAdvisor())
    .build();

chatClient.prompt().user("...").stream().content().subscribe(System.out::println);
```

逐片打码的原因：流式输出是分片的 `ChatResponse`，敏感词可能被切在两个 chunk 里——生产级实现需要做**跨片缓冲**（把上一片尾部与下一片头部拼接后再判断），上面是教学简化版。

## 4. 执行顺序

```java
chatClient.prompt().advisors(
    a -> a.advisors(memoryAdvisor, logAdvisor)   // 可同时挂多个
          .param(ChatMemory.CONVERSATION_ID, "42") // 给 Advisor 传运行时参数
).user("hi").call().content();
```

- `getOrder()` 越小越靠外：请求先过、响应后过
- 记忆类 Advisor 通常 order 较小（最先注入历史、最后保存新消息）

## 5. `.advisors(a -> a.param(ChatMemory.CONVERSATION_ID, id))` 什么意思

`a.param(key, value)` 是给本次调用的 Advisor **传运行时参数**，参数放在 `AdvisedRequest.adviseContext()` Map 里。

`ChatMemory.CONVERSATION_ID`（常量 `"chat_memory_conversation_id"`）是记忆 Advisor 约定的 key：它告诉 MessageChatMemoryAdvisor"这次属于哪个会话"，从而决定读写哪一段记忆。**挂了记忆 Advisor 后每次都要传它**，否则多个用户对话会串台。

## 6. 什么时候用 Advisor（完整系统中的分工）

| 放进 Advisor（切面） | 手写在业务代码 |
|---------------------|---------------|
| 记忆读写、日志、审计、敏感词 | 业务流程编排、分支决策 |
| 重试、限流、降级 | 事务、权限校验入口 |
| RAG 检索增强、提示词模板注入 | 与用户交互的 UI/返回码 |
| 对所有模型调用统一生效的横切逻辑 | 只对某个接口生效的逻辑 |

判据：**对所有（或大多数）模型调用统一生效的横切逻辑 → Advisor；与业务流程强绑定 → 手写**。

## 7. 预设 Advisor 好不好用

预设（MessageChatMemoryAdvisor、SimpleLoggerAdvisor、RetrievalAugmentationAdvisor、ToolCallAdvisor 等）覆盖了记忆/日志/RAG/工具的主干场景，**优先用预设**。需要自定义的典型场景：

- 敏感词/合规改写（本节案例）
- 质量门重问（03 案例）
- 公司特有的审计、灰度、多租户注入

约 80% 装配 + 20% 自定义，而不是反过来。

## 8. 生产边界

- 流式改写要考虑 chunk 边界切割问题
- after 钩子抛异常会影响整个链路，注意 try/catch
- Advisor 里不要放重业务逻辑，保持轻量（它是每次调用的热路径）
