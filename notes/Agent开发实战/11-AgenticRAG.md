# 11 Agentic RAG

## 1. 什么时候从标准 RAG 升级

标准 RAG 是固定的“检索一次再回答”；Agentic RAG 允许模型根据中间结果决定下一步：

```text
用户问题 -> 是否需要知识？
          -> 选择知识库或查询方式
          -> 评估结果是否足够
          -> 改写、补充检索或回答
```

它适合多个知识源、复杂问题拆解和需要基于结果继续行动的场景。问候、单知识库简单问答和强 SLA 场景通常不值得增加 Agent 决策。

## 2. 检索工具的接口设计

```python
@tool(response_format="content_and_artifact")
def retrieve_agent_knowledge(query: str) -> tuple[str, list[Document]]:
    """仅在问题涉及 Agent 知识时检索，并返回证据。"""
    return content, documents
```

模型看到的是 `content`，应用保留 `artifact`。原因是完整 Document 包含 metadata、内部 ID 或大量正文，不应该无条件进入上下文；但应用仍需要它来做引用、审计和二次校验。

工具描述应说明：何时调用、覆盖范围、没有结果时的含义、不要传入什么秘密。描述是选择依据，不是安全边界。

## 3. Agentic RAG 的典型循环

```text
question
  -> model decides retrieve
  -> retrieve(query)
  -> observation: documents/content
  -> model judges evidence
      -> enough: answer
      -> missing: rewrite and retrieve again
      -> impossible: say unknown
```

每轮都需要更新状态，而不是把所有结果无上限追加到消息历史。状态至少应包含原问题、当前 query、检索次数、候选来源、最终答案和终止原因。

## 4. 必须从代码限制 Agent

模型可能重复调用、不断改写或把无关问题送入检索。因此要同时限制：

- 最大检索次数和最大工具调用次数
- 单次 top-k、总文档数和上下文 token
- query 最大长度和改写次数
- 单请求总超时、模型调用预算和成本
- 重复 query、重复 source 和相同结果检测

练习中使用 `ToolCallLimitMiddleware(..., run_limit=2)`，这只是调用次数保护。它不能保证每次 query 有意义，也不能替代权限过滤和检索质量评测。

## 5. Query rewrite、multi-query 和结果评估

三种策略不要混为一谈：

| 策略 | 目的 | 成本 |
| --- | --- | --- |
| Query rewrite | 把口语问题改成更适合检索的表达 | 一次额外模型调用 |
| Multi-query | 从多个角度检索，再合并去重 | 多次检索和排序 |
| Result grading | 判断当前证据是否回答了问题 | 额外判断调用，可能降低误答 |

改写必须保留原问题的约束，不能把“只看某租户”改成全库查询。多查询结果合并时保留来源和权限标签，不能只合并正文。

## 6. 什么时候 Agentic RAG 反而更差

- 每个问题都必然需要同一个检索器。
- 需要严格、可预测的延迟和成本。
- 检索器本身已经是成熟的混合检索和重排系统。
- 文档少到一次检索就能覆盖。
- 模型无法可靠判断“证据是否足够”。

此时使用标准 RAG 或 LangGraph 固定流程更易验收。Agent 不是复杂度的默认升级按钮。

## 7. practice/15 的代码如何阅读

对应代码：[practice/15-agentic-rag](../../practice/15-agentic-rag/README.md)

`create_retrieval_tool` 把 VectorStore 包装成 Tool，`build_agent` 使用 `create_agent` 和工具调用上限，系统提示要求知识问题引用 source、常识问候不检索。测试重点是工具返回 `(content, artifact)` 的协议；真实集成测试才验证模型是否正确选择工具。

## 8. 可执行实验

准备三组输入：

```text
问候语：不应检索
“Runnable 支持哪些执行方式？”：应检索并引用 source
一个知识库没有的主题：应停止并回答不知道
```

把 `run_limit` 从 2 改成 1，观察复杂问题如何提前终止；再把工具描述删除一半，观察 Tool Selection 可能变化。实验结论应记录为“选择质量问题”还是“安全边界问题”。

## 9. Agentic RAG 的评测

至少分开测四件事：

```text
是否该检索 -> 工具选择准确率
检索问句是否合适 -> query 质量
证据是否包含答案 -> Recall@k / 人工标注
最终是否忠于证据 -> groundedness / answer correctness
```

只测最终答案无法知道是检索错还是生成错，也无法判断多轮检索是否真的带来收益。

## 10. 自测

1. 标准 RAG 和 Agentic RAG 的决策权分别在哪里？
2. 为什么工具调用上限不能只靠 Prompt 保证？
3. `artifact` 为什么适合应用保存而不是直接塞给模型？
4. Query rewrite 可能引入什么安全和语义风险？
5. 哪些场景应退回标准 RAG？

## 官方资料

- [Retrieval agents](https://docs.langchain.com/oss/python/langchain/retrieval)
- [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents)
