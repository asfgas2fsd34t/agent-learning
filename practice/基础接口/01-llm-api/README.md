# 练习 01：调用大模型 API

## 练习目标

完成一次最小的大模型调用，并能解释下面的数据流：

```text
读取环境变量
-> 创建模型客户端
-> 构造 messages
-> 发送 HTTP 请求
-> 解析模型响应
-> 输出最终文本
```

本练习暂时不包含 Tool Calling 和 Agent 循环，先把最基础的一次模型请求看懂、运行和调试。

## 目录结构

```text
01-llm-api/
├── .env.example
├── pyproject.toml
├── src/llm_api_practice/
│   ├── config.py    # 读取并校验环境变量
│   ├── chat.py      # 构造请求并调用模型
│   └── cli.py       # 接收用户输入并输出回答
└── tests/
    ├── test_config.py
    ├── test_chat.py
    └── test_cli.py
```

## 1. 安装依赖

所有练习共用仓库根目录的 Python 3.11 虚拟环境。在仓库根目录安装全部 workspace 包：

```bash
cd /Users/junjiezou/project/agent-learning
uv sync --all-packages --no-editable
```

`uv` 会读取 workspace 和各练习的 `pyproject.toml`，在仓库根目录创建 `.venv` 并安装：

- `openai`：调用 OpenAI-compatible API
- `python-dotenv`：从本地 `.env` 文件加载环境变量

## 2. 配置模型

```bash
cp .env.example .env
```

编辑 `.env`：

```dotenv
LLM_API_KEY=你的密钥
LLM_MODEL=服务商提供的模型名称
LLM_BASE_URL=服务商提供的兼容接口地址
```

注意：

- `.env` 已加入 `.gitignore`，不要提交真实密钥
- 使用默认 OpenAI 地址时，`LLM_BASE_URL` 可以留空
- 使用其他 OpenAI-compatible 服务时，按服务商文档填写模型名和地址

## 3. 运行程序

```bash
cd practice/基础接口/01-llm-api
uv run llm-chat
```

输入一个问题：

```text
请输入你的问题：什么是 Agent？
```

程序会输出模型回答。

## 4. 运行测试

测试不调用真实模型，也不会消耗 API 额度：

```bash
uv run python -m unittest discover -s tests -v
```

测试使用 `FakeClient` 替代真实客户端，验证：

- 缺少 API Key 时程序能够提前报错
- 缺少模型名称时程序能够提前报错
- 用户问题被正确放入 `messages`
- 模型回答被正确取出
- 模型返回空内容时程序不会静默继续
- 命令行能够完成输入、调用和输出

## 5. 重点阅读代码

### `config.py`

回答下面的问题：

```text
为什么 API Key 不能直接写在代码里？
为什么要在调用 API 前检查配置？
base_url 为什么允许为空？
```

### `chat.py`

重点观察：

```python
response = client.chat.completions.create(
    model=settings.model,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ],
)
```

需要理解：

- `model` 决定使用哪个模型
- `system` 消息定义模型的角色和行为
- `user` 消息保存本次用户问题
- `create` 发起真实网络请求
- `response.choices[0].message.content` 是模型返回的文本

### `cli.py`

`cli.py` 只负责流程编排：

```text
加载 .env
-> 读取配置
-> 接收用户问题
-> 调用 ask_model
-> 打印回答
```

它不负责模型请求的具体实现，这样每个文件只有一个清晰职责。

## 6. 本练习必须能回答的问题

完成练习后，需要能够独立说明：

1. 用户问题从哪里进入程序？
2. API Key 和模型名称从哪里读取？
3. HTTP 请求由哪一行代码发起？
4. `system` 和 `user` 消息分别有什么作用？
5. 模型回答从响应对象的哪个位置取出？
6. 为什么单元测试不应该真的调用模型 API？
7. 如果密钥错误、网络超时或模型名错误，应该去哪里排查？

## 下一步

练习 02 会在这个调用流程上加入第一个本地工具：

```text
query_sales(month, region)
```

届时模型不再只生成文本，还要选择工具并生成结构化参数。
