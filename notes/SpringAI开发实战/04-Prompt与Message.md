# 04 Prompt 与 Message

> 来源：Spring AI 官方文档 `api/prompt.html`（1.1.x）。

## 学习目标

- 理解 Prompt = List\<Message\> + ChatOptions
- 掌握 MessageType 四种角色
- 会用 PromptTemplate（模板渲染）
- 分清底层 ChatModel API 与 ChatClient 门面的关系

## 1. 核心心智模型

```text
Prompt = List<Message> + ChatOptions
Message = content + messageType + metadata（可带 Media）
ChatOptions = temperature、topP、model 等采样参数
```

ChatClient 的 `prompt()/user()/system()` 最终都会组装成 Prompt 交给 ChatModel。需要精确控制消息列表（比如工具消息、历史回放）时，直接用底层 API。

## 2. MessageType 四角色

| 类型 | 类 | 作用 |
|------|----|------|
| SYSTEM | SystemMessage | 系统人设、规则 |
| USER | UserMessage | 用户输入（可带 Media） |
| ASSISTANT | AssistantMessage | 模型回复（历史对话、工具思考） |
| TOOL | ToolMessage | 工具执行结果回传给模型 |

## 3. 底层 API 直接调用

```java
ChatResponse response = chatModel.call(
    new Prompt(
        List.of(
            new SystemMessage("你是一个简洁的中文助手"),
            new UserMessage("给我讲个笑话")
        ),
        OpenAiChatOptions.builder().temperature(0.7).build()
    )
);

// 取结果（getResults 返回 List<Generation>）
String text = response.getResult().getOutput().getText();
```

## 4. getResults() 返回什么

`ChatResponse.getResults()` 返回 `List<Generation>`：

```text
ChatResponse
└── generations: List<Generation>      // 多数情况只有 1 个
    └── Generation
        ├── output: AssistantMessage   // 模型说的话
        └── metadata: ChatGenerationMetadata（finishReason 等）

getResult() = getResults().get(0) 的快捷方式
```

多数时候只有一个 Generation（一次回答）；多候选（n>1）时会有多条。

## 5. PromptTemplate 模板渲染

```java
// 默认 StTemplateRenderer，占位符 {name}
PromptTemplate template = new PromptTemplate("给我讲一个关于 {topic} 的笑话");
Prompt prompt = template.create(Map.of("topic", "程序员"));

// 也可以换成 <> 语法（避免和 JSON/SpEL 冲突）
PromptTemplate template = new PromptTemplate("讲一个关于 <topic> 的笑话",
        StTemplateRenderer.builder().startDelimiterToken("<").endDelimiterToken(">").build());
```

ChatClient 里的等价写法：

```java
chatClient.prompt()
    .user(u -> u.text("帮我总结：{text}").param("text", article))
    .call().content();
```

## 6. 双层对照（什么时候用哪层）

| 需求 | 用哪层 |
|------|--------|
| 日常对话、结构化输出、挂 Advisor | ChatClient（01） |
| 手工拼消息列表（工具循环、历史回放、多模态精确控制） | ChatModel + Prompt |
| 在 Advisor 里改写消息 | 两边都会接触到 AdvisedRequest/Prompt |

记忆 Advisor 内部就是把历史 Message 列表插进 Prompt 的 system/user 前面（08）。

## 7. 生产边界

- 系统提示词与用户输入分离（SystemMessage / UserMessage），别拼成一个大字符串
- 渲染模板时对用户输入做转义，防止模板注入
- ChatOptions 优先放 builder 的 defaultOptions，单次调用只覆盖必要项
