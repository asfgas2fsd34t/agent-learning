# 练习 05：LangChain 基础

这个练习把原生模型调用改写为 LangChain 的基础组件，范围包括：

- `ChatOpenAI` 模型适配器
- `SystemMessage` 和 `HumanMessage`
- `ChatPromptTemplate`
- Runnable 的 `|` 组合
- Pydantic 结构化输出

对应笔记：[02 LangChain 基础](../../../notes/Agent开发实战/02-LangChain基础.md)

## 安装依赖

在项目根目录运行：

```powershell
python -m uv sync --all-packages --no-editable
```

## 配置模型

复制 `.env.example` 为 `.env`，填写：

```text
LLM_API_KEY=真实密钥
LLM_MODEL=模型名称
LLM_BASE_URL=OpenAI-compatible 接口地址
```

## 运行三个示例

进入当前练习目录：

```powershell
cd practice/Agent开发实战/01-langchain-basics
```

直接使用消息对象调用模型：

```powershell
python -m uv run langchain-basics --mode chat
```

运行“模板 -> 模型 -> 字符串解析器”链：

```powershell
python -m uv run langchain-basics --mode summary
```

运行 Pydantic 结构化输出链：

```powershell
python -m uv run langchain-basics --mode structured
```

一次运行全部流程：

```powershell
python -m uv run langchain-basics --mode all "Runnable 是 LangChain 的统一执行协议。"
```

也可以直接传入文本：

```powershell
python -m uv run langchain-basics --mode summary "LangChain 把模型、提示词和解析器组合成 Runnable。"
```

## 运行完整测试

先配置当前目录的 `.env`，然后运行一个完整的真实模型测试：

```powershell
python -m uv run python -m unittest discover -s integration_tests -v
```

这一个测试会把主要文件串起来：

```text
.env
-> cli.py 启动完整流程
-> config.py 读取配置
-> model.py 创建 ChatOpenAI
-> messages.py 构造消息并调用模型
-> chains.py 执行摘要链
-> structured.py 生成 StudyNote
```

测试会发起三次真实模型请求并消耗少量 token，不使用假回答。

`tests/` 中仍保留不调用 API 的单元测试，用于完整测试失败后定位具体模块；正常学习时只需要先运行上面的完整测试。

## 阅读顺序

1. `messages.py`：观察消息对象如何替代原生字典
2. `chains.py`：理解模板、模型、解析器的数据流
3. `structured.py`：理解 schema 如何约束模型输出
4. `cli.py`：观察三种调用方式如何接入真实模型
