# 练习 08：LangChain Agent

使用 LangChain v1 `create_agent()` 构建销售分析 Agent。Agent 可以多轮选择工具，最终返回自然语言回答。

```powershell
python -m uv sync --all-packages
cd practice/08-langchain-agent
python -m uv run langchain-agent "比较 2026-06 华东和华南销售额"
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[04 LangChain Agent](../../notes/Agent开发实战/04-LangChainAgent.md)

