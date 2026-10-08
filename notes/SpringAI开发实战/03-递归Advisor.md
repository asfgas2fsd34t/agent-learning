# 03 递归 Advisor

> 来源：Spring AI 官方文档 `api/advisors-recursive.html`（1.1.x）。

## 学习目标

- 理解递归 Advisor 的动机：拿到响应后不满意，可以"再来一次"
- 掌握 `CallAdvisorChain.copy(this)` 子链模式
- 掌握 maxRepeatAttempts 保险丝防死循环
- 了解内置递归组件 ToolCallAdvisor、StructuredOutputValidationAdvisor

## 1. 核心心智模型

```text
普通 Advisor：请求 → next → 响应（单程）
递归 Advisor：请求 → next → 检查响应 → 不合格就改写请求再 next（多程）
关键技术：chain.copy(this) 生成"从我之后开始"的子链，避免从头重跑
保险丝：maxRepeatAttempts 限制最大重复次数
```

适用：输出质量校验重问、工具循环、结构化输出重试修复。

## 2. 自定义案例：QualityGateAdvisor 质量门

响应长度不达标就重问，最多 3 次：

```java
public class QualityGateAdvisor implements CallAdvisor {

    private final int minWords;
    private final int maxRepeatAttempts;

    private QualityGateAdvisor(int minWords, int maxRepeatAttempts) {
        this.minWords = minWords;
        this.maxRepeatAttempts = maxRepeatAttempts;
    }

    @Override
    public AdvisedResponse adviseCall(AdvisedRequest request, CallAdvisorChain chain) {
        // 复制子链：copy(this) 表示"下次从我这里继续"，可再次进入本 Advisor
        CallAdvisorChain subChain = chain.copy(this);

        AdvisedRequest current = request;
        int attempts = 0;

        while (true) {
            AdvisedResponse response = subChain.next(current);
            String text = response.response().getResult().getOutput().getText();
            int words = text == null ? 0 : text.split("\\s+").length;

            if (words >= minWords || attempts >= maxRepeatAttempts) {
                return response;   // 合格或到达保险丝
            }

            attempts++;
            // 改写请求：让模型补充更详细的回答
            String retryText = current.userText()
                + "\n\n（上一次回答过于简短，请给出不少于 " + minWords + " 个词的详细回答）";
            current = AdvisedRequest.from(current)
                .userText(retryText)
                .build();
        }
    }

    @Override
    public int getOrder() { return 0; }

    @Override
    public String getName() { return "QualityGateAdvisor"; }

    public static Builder builder() { return new Builder(); }

    public static class Builder {
        private int minWords = 20;
        private int maxRepeatAttempts = 3;
        public Builder minWords(int v) { this.minWords = v; return this; }
        public Builder maxRepeatAttempts(int v) { this.maxRepeatAttempts = v; return this; }
        public QualityGateAdvisor build() {
            return new QualityGateAdvisor(minWords, maxRepeatAttempts);
        }
    }
}
```

使用：

```java
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(QualityGateAdvisor.builder().minWords(30).maxRepeatAttempts(3).build())
    .build();
```

## 3. 三个关键点

1. **`chain.copy(this)` vs `chain`**：直接用 `chain.next()` 是"继续后面的 Advisor"，第二次调用行为受限；`copy(this)` 得到的子链以"我"为起点，递归时整条后段链路（含模型调用）会重新执行。
2. **do-while / while(true) + 计数**：循环骨架就是"执行 → 检查 → 不行就改写请求再来"。
3. **maxRepeatAttempts 保险丝**：没有它，模型一直不合格就死循环烧钱。**必须有**。

## 4. 内置递归组件

### 4.1 ToolCallAdvisor

工具调用循环本身就是递归 Advisor：

```text
模型返回 tool_calls → 执行工具 → 把 ToolMessage 塞回请求 → 再次调用模型 → 直到无 tool_calls
```

相关参数：`returnDirect`（工具结果直接返回不经模型）、`disableMemory` / `conversationHistoryEnabled`（工具循环中是否计入记忆）。

### 4.2 StructuredOutputValidationAdvisor

结构化输出校验失败时，把解析错误信息发回模型要求修复重答（`entity()` 场景的自动重试），同样靠递归 + 重试上限。

## 5. 生产边界

- 重试上限必须设；同时考虑超时与成本（每次重试都是一次完整模型调用）
- 改写请求时保留原始用户意图，只附加修正指令，不要覆盖用户原话
- 递归 Advisor 与记忆 Advisor 组合时，注意中间失败轮次是否应写入记忆（通常不写）
