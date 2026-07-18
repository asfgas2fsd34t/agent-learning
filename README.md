# agent-learning

这个仓库用于记录 Agent 开发学习过程。

## 当前学习主线

- LLM 基础能力与局限性
- Prompt Engineering
- Agent 核心概念
- Agent 架构模式
- Tool Calling
- Memory
- RAG
- LangGraph
- MCP
- Agent 工程化与评测

## 笔记

### 大模型基础

- [大模型的能力与局限性笔记](notes/大模型基础/大模型的能力与局限性笔记.md)
- [Token 和上下文窗口笔记](notes/大模型基础/Token和上下文窗口笔记.md)
- [Transformer 基础笔记](notes/大模型基础/Transformer基础笔记.md)
- [从函数到 Transformer 重写整理笔记](notes/大模型基础/从函数到Transformer重写整理笔记.md)

### 提示词工程

- [提示词工程系统教程](notes/提示词工程/提示词工程系统教程.md)
- [提示词工程面试题 01-35](notes/提示词工程/提示词工程面试题%2001-35.md)

### Agent 基础

- [Agent 核心概念笔记](notes/Agent基础/Agent核心概念笔记.md)
- [Agent 架构模式笔记](notes/Agent基础/Agent架构模式笔记.md)
- [工具调用（Tool Calling）笔记](notes/Agent基础/工具调用ToolCalling笔记.md)
- [Agent 记忆系统（Memory）笔记](notes/Agent基础/Agent记忆系统Memory笔记.md)
- [Agent 基础四模块面试题](notes/Agent基础/Agent基础四模块面试题.md)
- [Agent 基础四模块面试标准答案](notes/Agent基础/Agent基础四模块面试标准答案.md)

### 后端基础

- [FastAPI 学习笔记](notes/FastAPI学习笔记.md)

## 编程实践

- [练习 01：调用大模型 API](practice/01-llm-api/README.md)
- [练习 02：手动实现 Tool Calling](practice/02-tool-calling/README.md)
- [练习 03：安全的写操作 Tool](practice/03-safe-write-tool/README.md)
- [练习 04：Agent 短期记忆](practice/04-agent-memory/README.md)

所有编程练习通过 `uv workspace` 共用根目录的 Python 3.11 虚拟环境和依赖锁文件：

```bash
uv sync --all-packages
```

PyCharm 统一选择：

```text
/Users/junjiezou/project/agent-learning/.venv/bin/python
```
