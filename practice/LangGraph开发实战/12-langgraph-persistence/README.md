# 补充练习 03：LangGraph 持久化与人工介入

实现退款审批图：校验请求、暂停等待人工审批、批准后执行或拒绝。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/LangGraph开发实战/12-langgraph-persistence
python -m uv run python -m unittest discover -s tests -v
```

对应笔记：[06 持久化机制与可恢复执行](../../../notes/LangGraph开发实战/06-持久化机制与可恢复执行.md)、[08 中断](../../../notes/LangGraph开发实战/08-中断.md)。
