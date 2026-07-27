# 补充练习 03：LangGraph 持久化与人工介入

实现退款审批图：校验请求、暂停等待人工审批、批准后执行或拒绝。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/Agent开发实战/12-langgraph-persistence
python -m uv run python -m unittest discover -s tests -v
```

相关主线笔记：[09 上下文与记忆](../../../notes/Agent开发实战/09-上下文与记忆.md)。本练习把其中的 Checkpointer 和人工介入单独演示出来。
