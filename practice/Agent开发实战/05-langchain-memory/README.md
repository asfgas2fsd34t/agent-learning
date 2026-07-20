# 练习 09：LangChain Memory

使用 `InMemorySaver` 和稳定 `thread_id` 保存 Agent 短期会话状态。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/Agent开发实战/05-langchain-memory
python -m uv run langchain-memory
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[06 上下文与 Memory](../../../notes/Agent开发实战/06-上下文与Memory.md)
