# 练习 08：Agent 安全与中间件

演示 `ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` 与业务权限校验的分工。

```powershell
python -m uv sync --all-packages --no-editable
cd practice/Agent开发实战/08-agent-middleware
python -m uv run guarded-agent "查询 2026-06 华东销售额"
python -m uv run python -m unittest discover -s tests -v
```

对应笔记：[08 中间件](../../../notes/Agent开发实战/08-中间件.md)、[12 Agent 安全与业务边界](../../../notes/Agent开发实战/12-Agent安全与业务边界.md)
