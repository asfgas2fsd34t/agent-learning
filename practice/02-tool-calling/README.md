# 练习 02：手动实现 Tool Calling

## 练习目标

不使用 LangChain 或 LangGraph，手动完成一次工具调用：

```text
用户问题
-> 模型选择 query_sales 并生成参数
-> Python 解析和校验参数
-> Python 执行本地销售查询
-> 工具结果返回模型
-> 模型生成最终回答
```

## 目录结构

```text
02-tool-calling/
├── .env.example
├── pyproject.toml
├── src/tool_calling_practice/
│   ├── config.py   # 读取 API 配置
│   ├── sales.py    # 真实工具：查询模拟销售数据
│   ├── tools.py    # 工具 Schema 和工具分发
│   ├── agent.py    # Tool Calling 编排流程
│   └── cli.py      # 命令行入口
└── tests/
```

## 1. 安装依赖

```bash
cd /Users/junjiezou/project/agent-learning
uv sync --all-packages
```

该命令会在仓库根目录创建共享 `.venv`，并安装所有练习包。

## 2. 配置模型

```bash
cp .env.example .env
```

填写与练习 01 相同的模型配置：

```dotenv
LLM_API_KEY=你的密钥
LLM_MODEL=gpt-5.4-mini
LLM_BASE_URL=https://aihub.firstshare.cn/v1
```

`.env` 已在仓库根目录的 `.gitignore` 中忽略。

## 3. 运行程序

```bash
cd practice/02-tool-calling
uv run sales-chat
```

可以测试：

```text
查询 2026 年 6 月华东区销售额
查询 2026 年 6 月华南区销售额
查询 2026 年 7 月华东区销售额
你好
```

本地模拟数据只包含：

| 月份 | 地区 | 销售额 |
|---|---|---:|
| 2026-05 | 华东 | 1,300,000 元 |
| 2026-06 | 华东 | 1,250,000 元 |
| 2026-06 | 华南 | 980,000 元 |
| 2026-06 | 华北 | 860,000 元 |

## 4. 第一次模型请求

`agent.py` 第一次请求会同时传入消息和工具定义：

```python
first_response = client.chat.completions.create(
    model=settings.model,
    messages=messages,
    tools=TOOLS,
    tool_choice="auto",
)
```

`tool_choice="auto"` 表示模型自己决定：

```text
需要真实销售数据 -> 请求工具
普通问候或不需要数据 -> 直接回答
```

模型请求工具时，返回的核心内容类似：

```json
{
  "id": "call_1",
  "type": "function",
  "function": {
    "name": "query_sales",
    "arguments": "{\"month\":\"2026-06\",\"region\":\"华东\"}"
  }
}
```

注意：`arguments` 是 JSON 字符串，不是 Python 字典，因此需要：

```python
arguments = json.loads(tool_call.function.arguments)
```

## 5. 谁真正执行工具

模型不会执行 `query_sales`。应用程序通过工具分发器执行：

```python
tool_result = execute_tool(tool_call.function.name, arguments)
```

职责关系：

```text
模型：选择 query_sales，生成 month 和 region
tools.py：确认工具名称并进行分发
sales.py：校验参数并查询真实数据
agent.py：组织完整调用流程
```

## 6. 为什么要加入两条消息

工具执行后，消息历史中必须加入：

### Assistant 工具请求

```json
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "call_1",
      "type": "function",
      "function": {
        "name": "query_sales",
        "arguments": "{\"month\":\"2026-06\",\"region\":\"华东\"}"
      }
    }
  ]
}
```

### Tool 执行结果

```json
{
  "role": "tool",
  "tool_call_id": "call_1",
  "content": "{\"success\":true,\"data\":{...}}"
}
```

`tool_call_id` 必须和模型请求中的 `id` 对应，这样模型才能知道结果属于哪一次工具调用。

## 7. 第二次模型请求

第二次请求包含完整消息历史：

```text
system
user
assistant（工具请求）
tool（执行结果）
```

模型读到工具结果后，才能生成自然语言答案。

## 8. 参数校验

`sales.py` 不信任模型参数，会检查：

- `month` 是否符合 `YYYY-MM`
- 月份是否真实
- `region` 是否属于支持范围
- 指定月份和地区是否有数据

工具统一返回结构化结果：

```json
{
  "success": false,
  "error_code": "NO_DATA",
  "message": "2026-07 华东没有销售数据",
  "retryable": false
}
```

## 9. 运行测试

```bash
uv run python -m unittest discover -s tests -v
```

测试不会调用真实 API，主要验证：

- 销售数据查询和参数校验
- 工具名称与参数 Schema
- 未知工具不能执行
- 模型直接回答时只请求一次
- 模型可以连续请求多轮工具
- 达到最大执行步数后停止
- Tool 结果正确关联 `tool_call_id`

### 真实模型测试

真实测试会读取本地 `.env`，调用实际模型并执行一次 Tool Calling，会消耗 API 额度，因此需要显式开启：

PowerShell：

```powershell
$env:RUN_LIVE_TESTS = "1"
uv run python -m unittest tests/test_live_api.py -v
```

真实测试文件为 `tests/test_live_api.py`。它会查询固定的 2026 年 6 月华东区销售额，并校验模型返回了对应数据。

## 10. Agent 循环

当前流程已经支持带最大步数保护的多轮工具调用：

```text
模型 -> 工具 -> 模型 -> 工具 -> 模型 -> 结束
```

核心代码在 `src/tool_calling_practice/agent.py`：

```python
for _ in range(max_steps):
    response = client.chat.completions.create(...)
    if not response.choices[0].message.tool_calls:
        return response.choices[0].message.content
    # 追加 assistant 消息和 tool 结果，进入下一轮
```

同时，`max_same_call` 会限制相同工具和相同参数的重复调用，并返回 `DUPLICATE_TOOL_CALL` 结构化错误。

当前还没有实现复杂重试策略和写操作幂等，这些属于后续生产化改造。

第 3 课对应的代码速查表：

[Agent 循环代码速查表](../../reference/Agent循环代码速查表.md)

第 4 课对应的代码速查表：

[重复调用与预算控制速查表](../../reference/重复调用与预算控制速查表.md)

```text
模型 -> 工具 -> 模型 -> 工具 -> ... -> 最终回答
```
