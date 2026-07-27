# 练习 02：LangSmith 可观测性

本练习使用不调用真实模型的 Runnable，理解 LangSmith Trace 的接入位置和运行配置：

- `LANGSMITH_TRACING`、`LANGSMITH_API_KEY` 和 `LANGSMITH_PROJECT`
- `run_name`、`tags`、`metadata`
- 如何用请求 ID 关联应用日志和 Trace
- 为什么 Trace 不能替代权限审计和业务日志

对应笔记：[03 LangSmith 的使用](../../../notes/Agent开发实战/03-LangSmith的使用.md)

## 运行

在项目根目录安装依赖：

```powershell
python -m uv sync --all-packages --no-editable
```

进入练习目录：

```powershell
cd practice/Agent开发实战/02-langsmith
```

运行本地示例。默认关闭上报，不需要 API Key：

```powershell
python -m uv run langsmith-practice "什么是 Agent？"
```

复制 `.env.example` 为 `.env`，填入真实 LangSmith Key 并设置：

```text
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=真实密钥
LANGSMITH_PROJECT=agent-learning
```

再次运行后，Runnable 的调用会自动创建 Trace。不要把 `.env` 或真实 Key 提交到 Git。

## 测试

```powershell
python -m uv run python -m unittest discover -s tests -v
```

测试使用本地 Runnable，不依赖网络，也不会消耗模型 Token。

## 阅读顺序

1. `src/langsmith_practice/tracing.py`：观察 Runnable 和 Trace config 的边界
2. `src/langsmith_practice/cli.py`：观察环境加载和请求 ID 的传入
3. `tests/test_tracing.py`：观察如何验证可观测性配置，而不是断言平台内部实现
