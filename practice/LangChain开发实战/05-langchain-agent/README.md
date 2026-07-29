# 练习 05：LangChain Agent

使用 LangChain v1 `create_agent()` 构建销售分析 Agent。Agent 可以多轮选择工具，最终返回自然语言回答。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/LangChain开发实战/05-langchain-agent
python -m uv run langchain-agent "比较 2026-06 华东和华南销售额"
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[07 智能体](../../../notes/LangChain开发实战/07-智能体.md)
