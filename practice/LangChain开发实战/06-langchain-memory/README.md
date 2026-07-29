# 练习 06：上下文与记忆

使用 `InMemorySaver` 和稳定 `thread_id` 保存 Agent 短期会话状态。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/LangChain开发实战/06-langchain-memory
python -m uv run langchain-memory
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[09 上下文与记忆](../../../notes/LangChain开发实战/09-上下文与记忆.md)
