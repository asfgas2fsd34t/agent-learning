# 00 Pydantic 前置知识

> 本篇提取自原有 Pydantic 学习笔记，是第 06 章结构化输出的前置补充。示例使用 Pydantic v2。

## 学习目标

- 理解类型标注和运行时校验的区别
- 掌握 `BaseModel`、`Field`、嵌套模型和可选字段
- 使用 `model_validate()`、`model_dump()` 和 `ValidationError`
- 理解类型转换、严格模式和自定义校验器
- 区分配置模型、传输模型和领域对象
- 理解 Pydantic 在 Tool、Structured Output 和 Agent 中的位置

## 1. 为什么 Agent 开发需要 Pydantic

Agent 系统中有大量不可信或不稳定的数据边界：

```text
HTTP 请求
模型结构化输出
Tool Call 参数
环境变量
数据库查询结果
第三方 API 响应
```

Python 类型标注只告诉开发工具“期望是什么类型”，默认不会在运行时阻止错误数据：

```python
def refund(amount: float) -> None:
    print(amount)


refund("not-a-number")  # Python 不会因为类型标注自动拒绝
```

Pydantic 会在数据进入系统边界时执行解析和校验：

```text
外部 dict / JSON
-> Pydantic 解析
-> 类型转换或严格校验
-> 字段规则校验
-> 自定义业务格式校验
-> 可靠的 Python 对象
```

## 2. 第一个 `BaseModel`

```python
from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int


user = User(name="张三", age=20)

print(user.name)
print(user.age)
print(type(user))
```

`BaseModel` 是 Pydantic 的基础模型类。子类的类型标注会被转换为字段定义。

### 2.1 从字典创建

```python
payload = {"name": "张三", "age": 20}
user = User.model_validate(payload)
```

也可以使用构造参数：

```python
user = User(**payload)
```

`model_validate()` 更明确地表达“校验外部数据”，适合服务边界。

### 2.2 从 JSON 创建

```python
json_text = '{"name": "张三", "age": 20}'
user = User.model_validate_json(json_text)
```

不要先手动 `json.loads()` 再校验，除非中间确实需要操作原始字典。

## 3. 必填、默认值和可空

```python
class Profile(BaseModel):
    username: str
    language: str = "zh-CN"
    email: str | None = None
```

| 定义 | 含义 |
|---|---|
| `username: str` | 必填且不能为 `None` |
| `language: str = "zh-CN"` | 可省略，默认使用 `zh-CN` |
| `email: str \| None = None` | 可省略，也允许显式传 `None` |
| `email: str \| None` | 必填，但值可以是 `None` |

“可选字段”和“值可以为空”不是同一个概念，是否有默认值决定字段能否省略。

## 4. `Field` 添加约束

```python
from pydantic import BaseModel, Field


class RefundRequest(BaseModel):
    order_id: str = Field(
        min_length=1,
        max_length=64,
        description="业务订单号",
    )
    amount: float = Field(
        gt=0,
        le=100_000,
        description="退款金额，单位为元",
    )
    reason: str = Field(
        min_length=2,
        max_length=200,
        description="退款原因",
    )
```

常用约束：

| 约束 | 作用 |
|---|---|
| `min_length` / `max_length` | 字符串或集合长度 |
| `pattern` | 字符串正则格式 |
| `gt` / `ge` | 大于 / 大于等于 |
| `lt` / `le` | 小于 / 小于等于 |
| `multiple_of` | 必须是指定数的倍数 |
| `description` | 字段说明，不是校验规则 |

下面的描述不会自动执行：

```python
amount: float = Field(description="金额必须大于 0")
```

必须同时写实际约束：

```python
amount: float = Field(gt=0, description="退款金额")
```

## 5. 类型转换与严格模式

Pydantic 默认会进行合理的类型转换：

```python
class Item(BaseModel):
    count: int


item = Item(count="12")
assert item.count == 12
```

这称为 Coercion。它方便接收表单、环境变量等字符串数据，但也可能掩盖调用方错误。

### 5.1 字段严格模式

```python
from pydantic import Field


class StrictItem(BaseModel):
    count: int = Field(strict=True)
```

### 5.2 模型严格模式

```python
from pydantic import BaseModel, ConfigDict


class StrictRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    count: int
    price: float
```

选择原则：

```text
用户表单、环境变量 -> 可以受控转换
Tool 写操作、支付、权限参数 -> 倾向严格校验
第三方兼容数据 -> 在 Adapter 层转换，内部保持严格
```

## 6. 枚举与 Literal

字段只能从有限集合中取值时，不要使用普通字符串：

```python
from typing import Literal


class Ticket(BaseModel):
    priority: Literal["low", "medium", "high"]
```

需要复用和附加行为时可以使用 Enum：

```python
from enum import StrEnum


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ticket(BaseModel):
    priority: Priority
```

这比在 Prompt 中写“请只返回 low、medium 或 high”更可靠。

## 7. 嵌套模型

```python
class Address(BaseModel):
    city: str
    district: str | None = None


class Customer(BaseModel):
    name: str
    address: Address


customer = Customer.model_validate(
    {
        "name": "张三",
        "address": {
            "city": "杭州",
            "district": "滨江区",
        },
    }
)
```

Pydantic 会递归创建和校验 `Address`。嵌套层级过深会增加 Tool Schema 和结构化输出难度，应尽量保持模型扁平、职责清晰。

### 7.1 列表嵌套

```python
class LineItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class Order(BaseModel):
    order_id: str
    items: list[LineItem]
```

## 8. 序列化

### 8.1 转换为字典

```python
data = customer.model_dump()
```

常用选项：

```python
customer.model_dump(exclude_none=True)
customer.model_dump(exclude_unset=True)
customer.model_dump(mode="json")
```

### 8.2 转换为 JSON

```python
json_text = customer.model_dump_json()
```

`model_dump(mode="json")` 会把日期、UUID、Enum 等转换为更适合 JSON 的值；默认 Python 模式可能保留对应 Python 对象。

## 9. 处理 `ValidationError`

```python
from pydantic import ValidationError


try:
    request = RefundRequest.model_validate(
        {
            "order_id": "A100",
            "amount": -1,
            "reason": "退款",
        }
    )
except ValidationError as exc:
    print(exc.errors())
```

`errors()` 返回结构化错误列表，通常包含：

```text
loc   错误字段路径
type  错误类型
msg   可读错误说明
input 原始输入
```

生产接口不要把完整异常和敏感输入直接返回给用户。应映射为稳定业务错误：

```python
{
    "code": "INVALID_REFUND_REQUEST",
    "message": "退款参数不合法",
    "fields": ["amount"],
}
```

## 10. 自定义字段校验器

```python
from pydantic import BaseModel, field_validator


class UserProfile(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("用户名不能为空")
        return normalized
```

`mode="before"` 在标准类型解析前执行，默认的 `after` 在解析后执行：

```python
@field_validator("username", mode="before")
@classmethod
def reject_non_string(cls, value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("用户名必须是字符串")
    return value
```

## 11. 跨字段校验

```python
from typing_extensions import Self
from pydantic import model_validator


class DateRange(BaseModel):
    start: int
    end: int

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end < self.start:
            raise ValueError("end 不能小于 start")
        return self
```

跨字段规则适合表达“结束时间不能早于开始时间”等模型内部不变量。

不要在校验器里执行数据库查询、远程 API 或写操作。Pydantic 校验应尽量纯粹、快速、可重复；资源归属和实时业务状态由 Service 层校验。

## 12. `dict`、dataclass 与 Pydantic

| 类型 | 类型提示 | 运行时校验 | 序列化 | 适合场景 |
|---|---|---|---|---|
| `dict` | 无固定结构 | 无 | 原生 | 临时数据、结构未知 |
| `TypedDict` | 有 | 默认无 | 原生 | 静态类型提示 |
| dataclass | 有 | 基础 | 需额外处理 | 内部领域对象 |
| Pydantic | 有 | 强 | 内置 | 外部输入输出边界 |

Pydantic 不一定要替代所有领域对象。它最适合系统边界。

## 13. JSON Schema

```python
schema = RefundRequest.model_json_schema()
```

Pydantic 可以从模型生成 JSON Schema。LangChain 会利用这些信息生成 Tool 参数或 Structured Output 声明：

```text
字段名
类型
是否必填
枚举和范围
description
嵌套结构
```

JSON Schema 是契约，不是业务执行器。即使 Schema 校验通过，仍需检查：

- 当前用户是否有权限操作订单
- 订单是否属于当前租户
- 退款金额是否超过可退金额
- 是否已经退款
- 是否需要人工确认

## 14. 模型分层

不要用一个 `BaseModel` 同时承担所有职责：

```text
API Request Model
-> Application Command
-> Domain Object
-> Persistence Model
-> API Response Model
```

示例：模型只提供业务意图参数：

```python
class RefundToolInput(BaseModel):
    order_id: str
    amount: float = Field(gt=0)
    reason: str
```

可信上下文由后端补充：

```python
class RefundCommand(BaseModel):
    user_id: str
    tenant_id: str
    order_id: str
    amount: float
    reason: str
    idempotency_key: str
```

`user_id`、`tenant_id` 和 `idempotency_key` 不应让模型生成。

## 15. Pydantic 在 LangChain 中的位置

### 15.1 Tool 参数

```python
from langchain_core.tools import tool


@tool(args_schema=RefundToolInput)
def refund_order(order_id: str, amount: float, reason: str) -> dict:
    """申请订单退款。"""
    ...
```

### 15.2 Structured Output

```python
structured_model = model.with_structured_output(RefundToolInput)
```

### 15.3 Agent 最终响应

```python
agent = create_agent(
    model=model,
    tools=tools,
    response_format=AnswerSchema,
)
```

Pydantic 负责数据形状与本地规则，模型负责生成候选数据，业务服务负责最终合法性。

## 16. 常见错误

### 16.1 把 description 当校验

只写说明不会限制数据，必须使用 `Field` 约束、Literal 或校验器。

### 16.2 所有字段都写成可选

为了避免模型校验失败而把所有字段设为 `None`，会把错误推迟到业务层。真正必需的字段应该保持必填。

### 16.3 校验通过就直接写库

格式合法不代表有权限、资源存在或状态允许。

### 16.4 过度类型转换

金额、权限和写操作参数应谨慎使用默认 Coercion。

### 16.5 Schema 过于复杂

深层嵌套、大量 Union 和数十个字段会降低模型生成成功率。必要时拆成多个步骤。

## 17. 自测

1. `age: int` 为什么不能阻止普通 Python 函数收到字符串？
2. `str | None` 与 `str | None = None` 有什么区别？
3. `description` 为什么不能代替 `gt=0`？
4. 什么场景应该开启严格模式？
5. Pydantic 校验通过后为什么仍要做权限校验？
6. Tool Schema 中为什么不应该包含 `user_id` 和幂等键？
7. `model_dump()` 与 `model_dump_json()` 有什么区别？

## 总结

```text
BaseModel：定义可校验的数据对象
Field：描述字段并声明真实约束
model_validate：校验 Python 数据
model_validate_json：直接校验 JSON
model_dump / model_dump_json：序列化
ValidationError：结构化校验错误
field_validator：单字段自定义规则
model_validator：跨字段规则
ConfigDict(strict=True)：严格模式
```

Pydantic 让外部数据进入 Python 系统时更可靠，但它不能替代权限、数据库约束和业务规则。
