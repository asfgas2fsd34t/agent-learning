# 练习 14：标准 RAG Chain

构建“问题 -> Retriever -> 带来源上下文 -> 模型回答”的标准 RAG。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/RAG开发实战/03-rag-chain
python -m uv run rag-chain "Runnable 是什么？"
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[02 RAG 技术实现](../../../notes/RAG开发实战/02-RAG技术实现.md)
