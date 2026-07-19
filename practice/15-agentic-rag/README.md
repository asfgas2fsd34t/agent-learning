# 练习 15：Agentic RAG

把 Retriever 包装为 Tool，让 LangChain Agent 决定是否检索知识库。

```powershell
python -m uv sync --all-packages
cd practice/15-agentic-rag
python -m uv run agentic-rag "Runnable 支持哪些执行方式？"
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[11 Agentic RAG](../../notes/Agent开发实战/11-AgenticRAG.md)

