# 练习 03：原生 Agent 循环

这个练习在不使用 LangChain 的情况下实现一个最小 Agent：

```text
模型请求
-> 模型选择 Tool
-> 应用执行 Tool
-> 把 Tool 结果放回 messages
-> 模型继续决策
-> 最终回答或达到上限
```

## 重点代码

- `agent.py`：循环、状态、最大步骤和重复调用保护
- `tools.py`：Tool Schema、工具分发和调用签名
- `sales.py`：确定性业务 Tool
- `tests/test_agent.py`：多轮 Tool Calling 和终止条件

## 运行测试

```powershell
python -m uv sync --all-packages
cd practice/03-agent-loop
python -m uv run python -m unittest discover -s tests -v
```

## 运行真实模型

复制 `.env.example` 为 `.env` 并填写模型配置，然后运行：

```powershell
python -m uv run agent-chat
```
