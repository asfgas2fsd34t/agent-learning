# FastAPI 学习笔记

这份笔记整理了目前已经学过的 FastAPI 前 11 课内容。

目标不是一次把 FastAPI 学得很深，而是先把做 Agent/AI 后端最常用的基础打牢。后面继续学习时，可以直接在这份笔记后面往下补。

## 第 1 课：FastAPI 最小程序

### 本课内容

- 如何创建 FastAPI 应用
- 如何定义一个最基本的 `GET` 接口
- 为什么返回 Python 字典会自动变成 JSON

### 核心理解

FastAPI 的起点很简单：创建应用对象，注册一个路由，再从函数里返回数据。

### 示例代码

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello FastAPI"}
```

### 重点

- `FastAPI()` 用来创建应用对象
- `@app.get("/")` 表示这个函数处理 `GET /`
- `async def` 表示异步接口函数
- 返回字典时，FastAPI 会自动转成 JSON

### 容易混淆

- `app` 表示整个后端服务
- `@app.get("/")` 不是普通函数调用，而是在注册路由

### 一句话总结

先学会一个应用、一个路由、一个 JSON 响应。

## 第 2 课：请求方法

### 本课内容

- `GET`、`POST`、`PUT`、`DELETE` 分别是什么意思
- 同一个路径为什么可以对应不同函数

### 核心理解

Web 接口不只是看路径，还要看请求方法。路径相同、方法不同，执行的函数也可以不同。

### 示例代码

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/books")
async def get_books():
    return {"action": "查询书籍"}


@app.post("/books")
async def create_book():
    return {"action": "新增书籍"}


@app.put("/books")
async def update_book():
    return {"action": "修改书籍"}


@app.delete("/books")
async def delete_book():
    return {"action": "删除书籍"}
```

### 重点

- `GET` 一般用于查询数据
- `POST` 一般用于新增数据
- `PUT` 一般用于修改数据
- `DELETE` 一般用于删除数据

### 容易混淆

- 路径可以一样，但请求方法不同，仍然是不同接口

### 一句话总结

先记住接口最基础的四个动作：查、增、改、删。

## 第 3 课：路径参数和查询参数

### 本课内容

- 如何从 URL 路径中取值
- 如何从查询字符串中取值
- FastAPI 如何自动做类型校验

### 核心理解

路径参数来自路由本身，查询参数来自 `?` 后面的部分。

### 示例代码 1：路径参数

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/books/{book_id}")
async def get_book(book_id: int):
    return {"book_id": book_id}
```

### 示例代码 2：查询参数

```python
@app.get("/search")
async def search_books(keyword: str, page: int = 1):
    return {"keyword": keyword, "page": page}
```

### 重点

- 路由中的 `{book_id}` 会映射到函数参数 `book_id`
- 没有默认值的参数是必填参数
- 有默认值的参数是可选参数
- FastAPI 会根据类型注解自动校验参数

### 容易混淆

- `GET /books/10` 是路径参数
- `GET /search?keyword=python&page=2` 是查询参数

### 一句话总结

路径参数写在路由里，查询参数写在 `?` 后面。

## 第 4 课：请求体和 `BaseModel`

### 本课内容

- 如何接收 JSON 请求体
- 如何用 Pydantic 模型定义请求数据
- 为什么 `BaseModel` 是 FastAPI 的核心能力之一

### 核心理解

当前端传来 JSON 数据时，FastAPI 可以借助 `BaseModel` 自动完成解析和校验。

### 示例代码

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Book(BaseModel):
    name: str
    price: float
    author: str


@app.post("/books")
async def create_book(book: Book):
    return {
        "message": "创建成功",
        "book": book
    }
```

### 重点

- `BaseModel` 用来定义 JSON 数据结构
- `book: Book` 表示请求体必须符合 `Book` 模型
- FastAPI 会自动检查字段是否存在、类型是否正确

### 容易混淆

- `book` 不只是普通字典，它会先经过模型校验
- 这种写法最常见于 `POST` 等提交数据的接口

### 一句话总结

用 `BaseModel` 来定义和校验 JSON 请求体。

## 第 5 课：`response_model`

### 本课内容

- 如何控制接口返回结构
- 如何避免敏感字段被返回
- 为什么请求模型和响应模型最好分开

### 核心理解

输入给后端的数据结构，和后端返回给前端的数据结构，不一定相同。`response_model` 就是用来约束输出结构的。

### 示例代码

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class UserCreate(BaseModel):
    username: str
    password: str
    age: int


class UserResponse(BaseModel):
    username: str
    age: int


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    return {
        "username": user.username,
        "password": user.password,
        "age": user.age
    }
```

### 重点

- `response_model` 用来定义最终返回结构
- 多余字段会被自动过滤
- 它有助于安全控制和接口文档生成

### 容易混淆

- 即使函数里返回了 `password`，只要 `UserResponse` 里没有，客户端最终也收不到

### 一句话总结

用 `response_model` 控制接口输出，让返回结果更安全、更稳定。

## 第 6 课：依赖注入 `Depends`

### 本课内容

- FastAPI 里的依赖注入是什么意思
- 如何复用公共逻辑
- 常见场景：token 校验、获取用户、分页参数

### 核心理解

`Depends` 的作用是：让 FastAPI 自动执行一个公共函数，并把结果注入到接口参数里。

### 示例代码 1：基础依赖

```python
from fastapi import Depends, FastAPI

app = FastAPI()


def get_name():
    return "alice"


@app.get("/demo")
async def demo(name: str = Depends(get_name)):
    return {"name": name}
```

### 示例代码 2：token 校验

```python
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()


def get_current_user(x_token: str = Header(...)):
    if x_token != "abc123":
        raise HTTPException(status_code=401, detail="token 无效")
    return {"username": "alice"}


@app.get("/me")
async def read_me(user=Depends(get_current_user)):
    return {"user": user}
```

### 重点

- `Depends(get_name)` 不是把函数本身传进去
- FastAPI 会执行依赖函数，并把执行结果传给参数
- 依赖函数本身也可以接收请求头、查询参数等

### 容易混淆

- `Depends` 不是手动调用函数
- 它适合处理多个接口都会用到的公共逻辑

### 一句话总结

多个接口都要用的逻辑，就考虑放进 `Depends`。

## 第 7 课：`HTTPException`

### 本课内容

- 如何返回标准 HTTP 错误
- 为什么错误不能伪装成普通 `200` 成功响应
- 初学阶段最常见的几个状态码

### 核心理解

当业务不满足条件时，不要假装成功返回数据，而是应该抛出真正的 HTTP 错误。

### 示例代码

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/books/{book_id}")
async def get_book(book_id: int):
    if book_id != 1:
        raise HTTPException(status_code=404, detail="书籍不存在")

    return {"book_id": 1, "name": "Python 入门"}
```

### 重点

- `raise HTTPException(...)` 会中断当前流程并返回错误响应
- 最常用的字段是 `status_code` 和 `detail`
- 初学阶段先记住：`400`、`401`、`403`、`404`、`500`

### 容易混淆

- `return {"error": "not found"}` 如果不配合真实状态码，本质上还是成功响应

### 一句话总结

接口出错时，用 `HTTPException` 返回标准错误。

## 第 8 课：中间件 `middleware`

### 本课内容

- 什么是中间件
- 如何在请求前后执行统一逻辑
- 常见场景：日志、耗时统计、统一响应头

### 核心理解

中间件包裹的是整个请求和响应流程，它处理的是全局行为，不是某一个单独接口的行为。

### 示例代码

```python
import time

from fastapi import FastAPI, Request

app = FastAPI()


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### 重点

- `await call_next(request)` 之前的代码在接口执行前运行
- `await call_next(request)` 之后的代码在接口执行后运行
- 中间件适合做统一处理

### 容易混淆

- 中间件和 `Depends` 不一样
- `Depends` 更偏向接口级公共逻辑
- 中间件更偏向整个请求响应生命周期

### 一句话总结

全局统一逻辑，优先考虑中间件。

## 第 9 课：`APIRouter`

### 本课内容

- 为什么要拆分路由
- 如何使用 `APIRouter`
- `prefix` 和 `tags` 的作用

### 核心理解

项目一旦变大，就不应该把所有接口都堆在一个文件里，而应该按业务拆成不同模块。

### 示例代码

```python
from fastapi import APIRouter, FastAPI

app = FastAPI()

user_router = APIRouter(prefix="/users", tags=["users"])
book_router = APIRouter(prefix="/books", tags=["books"])


@user_router.get("/")
async def get_users():
    return {"msg": "用户列表"}


@book_router.get("/")
async def get_books():
    return {"msg": "图书列表"}


app.include_router(user_router)
app.include_router(book_router)
```

### 重点

- `APIRouter()` 用来创建一个路由模块
- `include_router()` 用来把路由模块注册到主应用
- `prefix` 可以统一加路径前缀
- `tags` 可以帮助整理 `/docs` 文档分组

### 容易混淆

- `app` 是整个服务
- `router` 是服务里的某一组路由

### 一句话总结

`APIRouter` 是从小 demo 走向真实项目结构的第一步。

## 第 10 课：`Header`、`Form`、`File`、`UploadFile`

### 本课内容

- 如何接收请求头
- 如何接收表单数据
- 如何接收上传文件

### 核心理解

真实项目里，输入不一定都是 JSON。请求头、表单、文件上传都非常常见。

### 示例代码 1：请求头

```python
from typing import Optional

from fastapi import FastAPI, Header

app = FastAPI()


@app.get("/headers")
async def read_headers(x_token: Optional[str] = Header(None)):
    return {"x_token": x_token}
```

### 示例代码 2：表单和文件上传

```python
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI()


@app.post("/submit")
async def submit_file(
    username: str = Form(...),
    file: UploadFile = File(...)
):
    return {
        "username": username,
        "filename": file.filename
    }
```

### 重点

- `Header(...)` 表示从请求头取值
- `Form(...)` 表示从表单里取值
- `File(...)` 和 `UploadFile` 用来处理文件上传
- `await file.read()` 可以异步读取文件内容

### 容易混淆

- Python 里的 `x_token` 对应请求头里的 `x-token`
- 表单提交和 JSON 提交不是一回事
- 使用表单和文件上传时，通常要安装 `python-multipart`

### 一句话总结

不要只会 JSON，请求头、表单和文件上传也要尽早掌握。

## 第 11 课：状态码和 `JSONResponse`

### 本课内容

- 默认状态码和自定义状态码
- 什么时候直接返回字典
- 什么时候手动构造响应对象

### 核心理解

普通接口直接返回字典就够了，但当你需要更细地控制状态码、响应头和返回结构时，就要用响应对象。

### 示例代码 1：成功时指定状态码

```python
from fastapi import FastAPI

app = FastAPI()


@app.post("/users", status_code=201)
async def create_user():
    return {"message": "用户创建成功"}
```

### 示例代码 2：使用 `JSONResponse`

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/custom")
async def custom_response():
    return JSONResponse(
        status_code=200,
        content={"message": "自定义响应"},
        headers={"X-App-Name": "my-fastapi-app"}
    )
```

### 重点

- 正常成功返回一般是 `200`
- 创建资源常用 `201`
- `JSONResponse` 可以控制 `status_code`、`content`、`headers`

### 容易混淆

- 很多普通接口直接 `return {}` 就足够了
- 只有在需要更强控制时才用 `JSONResponse`

### 一句话总结

默认直接返回字典，需要更精细控制时再用 `JSONResponse`。

## 第 12 课：全局异常处理 `exception_handler`

### 本课内容

- 什么是全局异常处理
- 如何统一返回错误格式
- 如何接管 FastAPI 默认异常处理

### 核心理解

前面学的 `HTTPException` 更像是“单个接口里主动报错”。这一课学的是：当整个项目里不同地方都可能报错时，怎么统一处理返回格式。

### 示例代码 1：自定义业务异常

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


class UserNotFoundError(Exception):
    pass


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "code": 404,
            "message": "用户不存在",
            "data": None
        }
    )


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id != 1:
        raise UserNotFoundError()
    return {"id": 1, "name": "Alice"}
```

### 示例代码 2：接管请求校验异常

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "请求参数校验失败",
            "errors": exc.errors()
        }
    )
```

### 重点

- `@app.exception_handler(...)` 用来注册全局异常处理器
- 处理器一般接收 `request` 和 `exc`
- 可以统一定义项目错误返回格式
- `RequestValidationError` 是 FastAPI 常见的默认异常之一

### 容易混淆

- `HTTPException` 是在接口里直接抛
- `exception_handler` 是在全局统一接住并返回结果

### 一句话总结

项目一旦变大，就要用全局异常处理统一错误格式。

## 第 13 课：生命周期 `lifespan`

### 本课内容

- 什么是应用生命周期
- 应用启动前和关闭后可以做什么
- 为什么官方更推荐 `lifespan`

### 核心理解

有些逻辑不是每次请求都要执行，而是在应用启动时执行一次、关闭时再清理一次。这类逻辑就属于生命周期管理。

### 示例代码

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

ml_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ml_models["answer"] = "mock model loaded"
    print("app startup")
    yield
    ml_models.clear()
    print("app shutdown")


app = FastAPI(lifespan=lifespan)


@app.get("/predict")
async def predict():
    return {"model": ml_models["answer"]}
```

### 重点

- `lifespan` 用来处理启动和关闭逻辑
- `yield` 之前是启动阶段
- `yield` 之后是关闭阶段
- 适合加载模型、建立连接、初始化缓存、释放资源

### 容易混淆

- 生命周期逻辑不是给某个接口单独用的
- 它和中间件不同，中间件是每个请求都会经过

### 一句话总结

应用级初始化和清理逻辑，优先放进 `lifespan`。

## 第 14 课：鉴权基础

### 本课内容

- 什么是认证和鉴权
- FastAPI 里最常见的基础鉴权方式
- 如何使用 `OAuth2PasswordBearer`

### 核心理解

做后端时，很多接口不是谁都能访问。最基础的做法，就是让客户端带上 token，后端先拿到 token，再决定是否放行。

### 示例代码

```python
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    if token != "demo-token":
        raise HTTPException(status_code=401, detail="token 无效")
    return {"username": "alice"}


@app.get("/me")
async def read_me(user=Depends(get_current_user)):
    return {"user": user}
```

### 重点

- `OAuth2PasswordBearer` 会从请求中提取 Bearer Token
- 提取到的 token 仍然需要你自己校验
- 鉴权逻辑通常和 `Depends` 一起使用
- 这是后续 JWT、登录系统的基础

### 容易混淆

- 认证是“你是谁”
- 鉴权是“你有没有权限”
- `OAuth2PasswordBearer` 只负责帮你拿到 token，不负责自动验真

### 一句话总结

先掌握“拿 token + 校验 token”这条最基础的鉴权链路。

## 第 15 课：测试 `TestClient`

### 本课内容

- 为什么后端接口要写测试
- 如何使用 `TestClient`
- 如何测试 `GET`、`POST` 和带生命周期的应用

### 核心理解

测试的目标不是为了形式，而是为了确认接口行为是稳定的。FastAPI 可以通过 `TestClient` 在不真正启动服务器的情况下直接测试接口。

### 示例代码 1：基础接口测试

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "hello"}


client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}
```

### 示例代码 2：测试 `POST`

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()


class Book(BaseModel):
    name: str
    price: float


@app.post("/books")
async def create_book(book: Book):
    return {"name": book.name, "price": book.price}


client = TestClient(app)


def test_create_book():
    response = client.post(
        "/books",
        json={"name": "Python", "price": 59.9}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Python"
```

### 示例代码 3：测试生命周期

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

items = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    items["foo"] = {"name": "bar"}
    yield
    items.clear()


app = FastAPI(lifespan=lifespan)


@app.get("/items")
async def read_items():
    return items


def test_lifespan():
    with TestClient(app) as client:
        response = client.get("/items")
        assert response.status_code == 200
        assert response.json() == {"foo": {"name": "bar"}}
```

### 重点

- `TestClient(app)` 可以直接测试 FastAPI 应用
- 测试函数通常以 `test_` 开头
- 发请求的方法和 `httpx` 很像
- 如果要让 `lifespan` 生效，常用 `with TestClient(app) as client`

### 容易混淆

- 测试时不需要单独先启动 `uvicorn`
- 异步应用也能用普通测试函数配合 `TestClient`

### 一句话总结

先学会用 `TestClient` 测最关键的接口行为。

## 第 16 课：项目结构实战

### 本课内容

- 为什么真实项目不能一直写单文件
- 如何把项目拆成多个文件
- `routers`、`dependencies`、`main.py` 分别适合放什么

### 核心理解

随着接口变多，项目一定会从“一个文件”走向“多个模块”。核心思路就是：主入口负责组装，业务接口拆到不同路由文件，共享逻辑拆到独立依赖文件。

### 推荐结构

```text
app/
├── __init__.py
├── main.py
├── dependencies.py
└── routers/
    ├── __init__.py
    ├── users.py
    └── items.py
```

### 示例代码 1：`main.py`

```python
from fastapi import FastAPI

from app.routers import items, users

app = FastAPI()

app.include_router(users.router)
app.include_router(items.router)
```

### 示例代码 2：`dependencies.py`

```python
from fastapi import Header, HTTPException


def get_token_header(x_token: str = Header(...)):
    if x_token != "demo-token":
        raise HTTPException(status_code=400, detail="X-Token 无效")
```

### 示例代码 3：`routers/users.py`

```python
from fastapi import APIRouter, Depends

from app.dependencies import get_token_header

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_token_header)]
)


@router.get("/")
async def read_users():
    return [{"username": "alice"}]
```

### 重点

- `main.py` 负责创建应用并注册路由
- `routers/` 负责按业务拆接口
- `dependencies.py` 负责放共享依赖
- `__init__.py` 让目录成为可导入的 Python 包

### 容易混淆

- 项目结构不是越复杂越好，而是按业务逐步拆分
- 刚开始只拆 `main.py + routers + dependencies` 就已经足够实用了

### 一句话总结

项目结构实战的核心，是把“应用入口、业务路由、共享逻辑”分开。

## 当前学习进度总结

目前主线已经学到：

1. 最小可运行程序
2. 请求方法
3. 路径参数和查询参数
4. 请求体 `BaseModel`
5. `response_model`
6. `Depends`
7. `HTTPException`
8. `middleware`
9. `APIRouter`
10. `Header`、`Form`、`File`
11. 状态码和 `JSONResponse`
12. 全局异常处理 `exception_handler`
13. 生命周期 `lifespan`
14. 鉴权基础
15. 测试 `TestClient`
16. 项目结构实战

这 16 课已经覆盖了从 FastAPI 入门，到能写一个结构清晰、带基础鉴权和测试的后端项目所需的主干知识。

## 下一步建议学习

建议后面继续学：

1. JWT 鉴权和登录流程
2. 数据库集成，例如 SQLAlchemy 或 SQLModel
3. 异步数据库操作
4. 文件存储和对象存储
5. BackgroundTasks、消息队列
6. 部署与生产环境配置

## 快速复习规则

- JSON 请求体优先用 `BaseModel`
- 想控制输出结构就用 `response_model`
- 公共逻辑优先考虑 `Depends`
- 正确返回错误要用 `HTTPException`
- 整个应用级别的统一处理用中间件
- 项目一大就开始用 `APIRouter`
- 启动和关闭逻辑优先用 `lifespan`
- 鉴权逻辑通常和 `Depends` 一起组合使用
- 写完关键接口后，尽量补一个 `TestClient` 测试

## 最后说明

这个阶段最重要的不是追求高级，而是把每一个基础知识点真正理解清楚：它是什么、什么时候用、和别的概念有什么区别。等这 16 课都比较顺了，再往数据库、JWT、部署这些方向继续扩展，会轻松很多。
