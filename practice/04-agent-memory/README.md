# 练习 04：Agent 短期记忆

这个练习使用 SQLite 保存会话历史，并在下一轮模型请求中重新加载，从而实现可持久化的短期记忆。

## 核心流程

```text
读取 conversation_id 的最近消息
-> 组装 system + history + 当前问题
-> 调用大模型
-> 保存 user 和 assistant 消息
-> 下一轮继续加载
```

## 运行测试

```powershell
python -m uv sync --all-packages
cd practice/04-agent-memory
python -m uv run python -m unittest discover -s tests -v
```

## 运行真实对话

复制 `.env.example` 为 `.env` 并配置模型，然后运行：

```powershell
python -m uv run memory-chat
```

输入相同的会话 ID，可以在程序重启后继续读取之前的对话。
