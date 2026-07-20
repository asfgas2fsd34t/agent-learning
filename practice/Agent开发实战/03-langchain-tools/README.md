# 练习 07：LangChain Tools

使用 `@tool` 定义销售查询工具，并手动完成“模型请求工具 -> 应用执行 -> ToolMessage -> 最终回答”。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/Agent开发实战/03-langchain-tools
python -m uv run langchain-tools "查询 2026-06 华东销售额"
python -m uv run python -m unittest discover -s tests -v
python -m uv run python -m unittest discover -s integration_tests -v
```

对应笔记：[04 LangChain Tools](../../../notes/Agent开发实战/04-LangChainTools.md)
