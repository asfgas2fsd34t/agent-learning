# 练习 04：原生 Agent Memory

这个练习使用 SQLite 保存短期会话历史，并在下一轮请求前重新加载相关消息。

```text
读取 conversation_id 的最近消息
-> system + history + 当前问题
-> 调用模型
-> 保存 user 和 assistant 消息
```

## 运行测试

```powershell
python -m uv sync --all-packages --no-editable
cd practice/基础接口/04-agent-memory
python -m uv run python -m unittest discover -s tests -v
```

## 运行真实对话

复制 `.env.example` 为 `.env` 并配置模型：

```powershell
python -m uv run memory-chat
```

相同的会话 ID 会读取同一份历史记录。`.data/` 目录已加入 Git 忽略，不会提交 SQLite 数据库。
