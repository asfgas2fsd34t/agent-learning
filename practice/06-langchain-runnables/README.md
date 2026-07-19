# 练习 06：Runnable 与 LCEL 深入

本练习使用一条真实可执行的自适应摘要链，练习：

- `RunnableLambda`
- `RunnablePassthrough.assign()`
- `RunnableParallel`
- `RunnableBranch`
- `RunnableSequence`
- `invoke()`、`batch()`、`stream()`

对应笔记：[02 Runnable 与 LCEL 深入](../../notes/Agent开发实战/02-Runnable与LCEL深入.md)

## 安装依赖

在项目根目录运行：

```powershell
python -m uv sync --all-packages
```

## 配置模型

在当前目录配置 `.env`：

```text
LLM_API_KEY=真实密钥
LLM_MODEL=模型名称
LLM_BASE_URL=OpenAI-compatible 接口地址
```

## 运行真实 Chain

进入练习目录：

```powershell
cd practice/06-langchain-runnables
```

单条自适应摘要：

```powershell
python -m uv run langchain-runnables --mode summary "Runnable 是 LangChain 的统一执行协议。"
```

较长文本会自动走长文本 Prompt，短文本走短文本 Prompt。

批量执行：

```powershell
python -m uv run langchain-runnables --mode batch
```

流式执行：

```powershell
python -m uv run langchain-runnables --mode stream "请流式总结 Runnable 的作用。"
```

一次运行三个模式：

```powershell
python -m uv run langchain-runnables --mode all
```

## 测试

先运行不消耗 token 的单元测试：

```powershell
python -m uv run python -m unittest discover -s tests -v
```

再运行真实端到端测试：

```powershell
python -m uv run python -m unittest discover -s integration_tests -v
```

真实测试会调用模型，验证完整链能够执行单次、批量和流式流程。批量和流式能力依赖具体模型服务，不能只根据模型类是否存在相关方法来判断。

## 文件阅读顺序

1. `src/langchain_runnables/runnables.py`：观察每种 Runnable 如何组合
2. `src/langchain_runnables/chains.py`：观察分支 Chain 的整体结构
3. `src/langchain_runnables/cli.py`：观察 `invoke/batch/stream` 的入口
4. `tests/`：观察如何用假模型测试 Chain 结构
5. `integration_tests/`：观察如何用真实模型做端到端验证

