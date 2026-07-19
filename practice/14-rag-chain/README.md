# 练习 14：标准 RAG Chain

构建“问题 -> Retriever -> 带来源上下文 -> 模型回答”的标准 RAG。

```powershell
python -m uv sync --all-packages
cd practice/14-rag-chain
python -m uv run rag-chain "Runnable 是什么？"
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[10 Retriever 与标准 RAG](../../notes/Agent开发实战/10-Retriever与标准RAG.md)

