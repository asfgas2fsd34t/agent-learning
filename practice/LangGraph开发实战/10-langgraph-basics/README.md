# 补充练习 01：LangGraph 基础

使用 State、Node、Edge 构建“规划提纲 -> 生成草稿”的单 Agent 图。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/LangGraph开发实战/10-langgraph-basics
python -m uv run langgraph-basics "Runnable"
python -m uv run python -m unittest discover -s tests -v
```

对应笔记：[01 LangGraph 总览](../../../notes/LangGraph开发实战/01-LangGraph总览.md)、[02 图的基础构建与运行](../../../notes/LangGraph开发实战/02-图的基础构建与运行.md)、[03 图的状态管理](../../../notes/LangGraph开发实战/03-图的状态管理.md)。
