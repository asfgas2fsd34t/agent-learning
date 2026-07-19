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
- [00 Pydantic 基础：让外部数据变成可靠对象](notes/Agent开发实战/00-Pydantic基础.md)
- [01 LangChain 基础：从原生调用到可组合链](notes/Agent开发实战/01-LangChain基础.md)
- [02 Runnable 与 LCEL 深入](notes/Agent开发实战/02-Runnable与LCEL深入.md)
- [03 LangChain Tools](notes/Agent开发实战/03-LangChainTools.md)
- [04 LangChain Agent](notes/Agent开发实战/04-LangChainAgent.md)
- [05 上下文与 Memory](notes/Agent开发实战/05-上下文与Memory.md)
- [06 生产级工具集成](notes/Agent开发实战/06-生产级工具集成.md)
- [07 Agent 安全与中间件](notes/Agent开发实战/07-Agent安全与中间件.md)
- [08 文档加载与切分](notes/Agent开发实战/08-文档加载与切分.md)
- [09 Embedding 与向量存储](notes/Agent开发实战/09-Embedding与向量存储.md)
- [10 Retriever 与标准 RAG](notes/Agent开发实战/10-Retriever与标准RAG.md)
- [11 Agentic RAG](notes/Agent开发实战/11-AgenticRAG.md)
- [12 LangGraph 基础](notes/Agent开发实战/12-LangGraph基础.md)
- [13 LangGraph 进阶流程](notes/Agent开发实战/13-LangGraph进阶流程.md)
- [14 持久化与人工介入](notes/Agent开发实战/14-持久化与人工介入.md)
- [15 调试、评测与性能优化](notes/Agent开发实战/15-调试评测与性能优化.md)

### 后端基础

- [FastAPI 学习笔记](notes/FastAPI学习笔记.md)

## 编程实践

- [练习 01：调用大模型 API](practice/01-llm-api/README.md)
- [练习 02：手动实现 Tool Calling](practice/02-tool-calling/README.md)
- [练习 03：原生 Agent 循环](practice/03-agent-loop/README.md)
- [练习 04：原生 Agent Memory](practice/04-agent-memory/README.md)
- [练习 05：LangChain 基础](practice/05-langchain-basics/README.md)
- [练习 06：Runnable 与 LCEL 深入](practice/06-langchain-runnables/README.md)
- [练习 07：LangChain Tools](practice/07-langchain-tools/README.md)
- [练习 08：LangChain Agent](practice/08-langchain-agent/README.md)
- [练习 09：LangChain Memory](practice/09-langchain-memory/README.md)
- [练习 10：生产级工具集成](practice/10-production-tools/README.md)
- [练习 11：Agent 安全与中间件](practice/11-agent-middleware/README.md)
- [练习 12：文档加载与切分](practice/12-document-processing/README.md)
- [练习 13：Embedding 与向量存储](practice/13-vector-store/README.md)
- [练习 14：标准 RAG Chain](practice/14-rag-chain/README.md)
- [练习 15：Agentic RAG](practice/15-agentic-rag/README.md)
- [练习 16：LangGraph 基础](practice/16-langgraph-basics/README.md)
- [练习 17：LangGraph 进阶流程](practice/17-langgraph-workflow/README.md)
- [练习 18：持久化与人工介入](practice/18-langgraph-persistence/README.md)
- [练习 19：Agent 调试与评测](practice/19-agent-evaluation/README.md)

所有编程练习通过 `uv workspace` 共用根目录的 Python 3.11 虚拟环境和依赖锁文件：

```bash
uv sync --all-packages
```

PyCharm 统一选择：

```text
/Users/junjiezou/project/agent-learning/.venv/bin/python
```
