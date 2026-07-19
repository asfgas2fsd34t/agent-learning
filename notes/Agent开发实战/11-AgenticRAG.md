# 11 Agentic RAG

## 学习目标

让 Agent 根据问题决定是否检索，而不是每个问题固定执行 RAG。

## 与标准 RAG 的区别

```text
标准 RAG：每次问题都检索一次，再回答
Agentic RAG：模型判断是否检索、检索什么、是否需要再次检索
```

适合 Agentic RAG 的场景：

- 有多个知识库或检索工具
- 部分问题不需要外部知识
- 问题需要拆分成多个检索查询
- 首次检索质量不足，需要改写后再次检索

## 检索 Tool

```python
@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """检索 Agent 开发知识库。"""
    docs = retriever.invoke(query)
    content = format_documents(docs)
    return content, docs
```

`content` 给模型阅读，`artifact` 保留原始 `Document` 供应用记录来源。

## 调用限制

Agentic RAG 增加了不确定性，必须限制：

- 检索次数
- 每次 Top-K
- 总上下文 token
- 查询改写次数
- 无结果时的停止规则

## 质量检查

模型自我反思可以帮助发现明显缺口，但不能代替离线评测。检索质量应使用命中率、MRR、nDCG 等数据指标和人工标注问题集验证。

## 对应实践

[practice/15-agentic-rag](../../practice/15-agentic-rag/README.md) 将 Retriever 包装为 Tool，再用 `create_agent()` 让模型决定是否调用。

## 自测

1. 哪些问题不需要检索？
2. `artifact` 为什么不直接塞进模型上下文？
3. 如何防止 Agent 无限改写和检索？
4. 自我反思为什么不能代替评测集？

