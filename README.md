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

### Agent 开发实战

- [Agent 开发实战学习路径](notes/Agent开发实战/README.md)
- [01 Pydantic 基础：让外部数据变成可靠对象](notes/Agent开发实战/01-Pydantic基础.md)
- [02 LangChain 基础：从原生调用到可组合链](notes/Agent开发实战/02-LangChain基础.md)
- [03 Runnable 与 LCEL 深入](notes/Agent开发实战/03-Runnable与LCEL深入.md)
- [04 LangChain Tools](notes/Agent开发实战/04-LangChainTools.md)
- [05 LangChain Agent](notes/Agent开发实战/05-LangChainAgent.md)
- [06 上下文与 Memory](notes/Agent开发实战/06-上下文与Memory.md)
- [07 生产级工具集成](notes/Agent开发实战/07-生产级工具集成.md)
- [08 Agent 安全与中间件](notes/Agent开发实战/08-Agent安全与中间件.md)
- [09 LangGraph 基础](notes/Agent开发实战/09-LangGraph基础.md)
- [10 LangGraph 进阶流程](notes/Agent开发实战/10-LangGraph进阶流程.md)
- [11 持久化与人工介入](notes/Agent开发实战/11-持久化与人工介入.md)
- [12 调试、评测与性能优化](notes/Agent开发实战/12-调试评测与性能优化.md)

### RAG 开发实战

- [RAG 开发实战学习路径](notes/RAG开发实战/README.md)
- [01 RAG 基础概念与核心组件](notes/RAG开发实战/01-RAG基础概念与核心组件.md)
- [02 RAG 技术实现](notes/RAG开发实战/02-RAG技术实现.md)

### 后端基础

- [FastAPI 学习笔记](notes/FastAPI学习笔记.md)

## 编程实践

- [基础接口与原生机制](practice/基础接口/README.md)
- [Agent 开发实战](practice/Agent开发实战/README.md)
- [RAG 编程实践目录](practice/RAG开发实战/README.md)

所有编程练习通过 `uv workspace` 共用根目录的 Python 3.11 虚拟环境和依赖锁文件：

```bash
uv sync --all-packages --no-editable
```

PyCharm 统一选择：

```text
/Users/junjiezou/project/agent-learning/.venv/bin/python
```
