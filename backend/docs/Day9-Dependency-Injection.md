# Day 9 · FastAPI 依赖注入（Dependency Injection）

> 配套代码已写入你的工程（可直接运行）：
> - `backend/app/database.py` → 新增 `get_db()`
> - `backend/app/dependencies.py` → 新增 `get_current_user()`（假用户）、`require_admin()`
> - `backend/app/api/routes/protected.py` → 演示路由 `/me`、`/me/admin`、`/me/ping-db`
> - `backend/app/main.py` → 已挂载上面的路由
> - 依赖 `sqlalchemy>=2.0.54` 已通过 `uv add` 安装

## 0. 一句话目标

学会用 `Depends()` 把「当前登录用户」和「数据库 Session」做成**可复用、可注入、可替换**的依赖；并真正理解**为什么不该在每个接口里自己 `new` 一个 Session**。

## 1. 什么是依赖注入（DI）

**没有 DI 的写法（直觉写法）：**

```python
@app.get("/me")
def me():
    db = SessionLocal()          # 每个接口都自己造
    user = get_current_user()    # 每个接口都自己调
    try:
        ...
    finally:
        db.close()               # 还容易忘记关
```

问题：

- 重复：10 个接口写 10 遍。
- 难测试：想换成测试库？得改 10 个地方。
- 生命周期混乱：谁负责关连接？忘了就泄漏。

**DI 的写法：**

```python
@app.get("/me")
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ...
```

你只**声明需要什么**（`db`、`user`），FastAPI 负责**怎么造、何时造、何时销毁**。函数 `get_db` / `get_current_user` 就叫「依赖」。

你的工程里 `app/api/routes/devices.py` 其实早就用过了——`verify_device_token` 就是个依赖，而且挂在整条路由上：

```python
router = APIRouter(prefix="/devices", dependencies=[Depends(verify_device_token)])
```

所以 Day 9 不是从零学，是把你已经会的一点系统化。

## 2. Depends() 怎么运转

要点：

- 依赖可以是**普通函数**，返回值会被注入到对应参数。
- 依赖参数也能**再依赖别的依赖**（嵌套）。
- 用 `yield` 的依赖，FastAPI 会在请求结束后执行 `yield` 之后的代码（用来做清理，比如 `db.close()`）。

（请求流转图见下方「图示 1：DI 请求流转」）

## 3. 实战①：get_db() —— 每个请求一个 Session

`backend/app/database.py`（节选）：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db          # 把 Session 交给接口用
    finally:
        db.close()        # 请求结束，归还连接
```

## 4. 核心目标：为什么 Session 不该每个接口自己 new

这是今天最重要的结论。先看清两个**常见误区**：

### 误区 A：全局复用一个 Session（跨请求共享）

```python
# 千万别这么做
db = SessionLocal()   # 模块级全局变量

@app.get("/a")
def a():
    return db.query(...)   # 请求1用它
@app.get("/b")
def b():
    return db.query(...)   # 请求2也用它
```

`Session` **不是线程安全的**。FastAPI 默认用线程池跑同步接口，并发请求会同时碰同一个 Session → 数据错乱、幽灵提交、`Session is already flushed` 之类的诡异报错。

### 误区 B：每个接口自己 new 但忘了关

```python
@app.get("/x")
def x():
    db = SessionLocal()   # new 了一个
    return db.query(...)  # 用完没 close
```

每个 `SessionLocal()` 会向连接池**借一条数据库连接**，只有 `close()` 才归还。你借了不还会怎样？

- 连接池大小有限（SQLAlchemy 默认 5 条 + 少量溢出）。
- 请求多了，池被借光 → 新请求阻塞等待 → 最终 `TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out`。
- 这就是「连接泄漏」。

### 正解：每请求一个 Session，用完即还（get_db 做的事）

把 Session 的「造」和「毁」集中到一个 `yield` 依赖里：

- 每个请求得到**自己专属**的 Session（线程安全 ✓）。
- 请求结束 `finally: db.close()` 把连接**归还**给池（不泄漏 ✓）。
- 事务边界自然对齐「一次 HTTP 请求 = 一个工作单元」（✓）。
- 测试时只需 `app.dependency_overrides[get_db] = 我的测试依赖`，就能换成内存 SQLite（✓ 可测试）。

（两种做法对比见下方「图示 2：Session 生命周期对比」）

一句话记忆：**Session 要「短命、私有、自动回收」，不要「长寿共享」也不要「随手 new 随手丢」。**

## 5. 实战②：get_current_user() —— 先写假用户

`backend/app/dependencies.py`：

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    is_active: bool = True
    is_admin: bool = False

FAKE_USER = User(id=1, username="yyx", is_active=True, is_admin=True)

def get_current_user(x_user_id: int | None = Header(default=None, alias="X-User-Id")) -> User:
    # 学习阶段：直接返回假用户
    if x_user_id is None:
        return FAKE_USER
    return User(id=x_user_id, username=f"user-{x_user_id}", is_active=True)

def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
```

注意 `require_admin` **依赖 `get_current_user`**——这就是依赖嵌套。FastAPI 会先解析内层，把结果注入外层，再跑外层校验。

真实项目里 `get_current_user` 应改成：从 `Authorization` 头取 Bearer Token → 验签 → 用里面的 user_id 查库 → 查不到/禁用就 `raise 401`。现在先写死，把 DI 的机制练熟。

## 6. 把依赖用起来

`backend/app/api/routes/protected.py`：

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import User, get_current_user, require_admin

router = APIRouter(prefix="/me", tags=["当前用户（演示 DI）"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("")
def read_me(user: CurrentUser):
    return user

@router.get("/admin")
def read_admin(user: Annotated[User, Depends(require_admin)]):
    return {"message": f"你好，管理员 {user.username}"}

@router.get("/ping-db")
def ping_db(db: DbSession):
    return {"db_state": "Session 已注入且可用", "in_transaction": db.in_transaction()}
```

`Annotated[Session, Depends(get_db)]` 是推荐写法：把「类型 + 依赖」打包成一个别名，接口签名既干净又有类型提示。

## 7. 跑起来验证

```bash
cd E:/Codes/atlas-ai/backend
uv run uvicorn app.main:app --reload
```

打开 http://127.0.0.1:8000/docs ：

- `GET /me` → 直接返回假用户 `{"id":1,"username":"yyx",...}`。
- `GET /me/admin` → 因为假用户是管理员，返回成功；把 `FAKE_USER` 的 `is_admin` 改成 `False` 再试，会得到 403。
- `GET /me/ping-db` → 返回 `{"db_state":"Session 已注入且可用","in_transaction":false}`，证明 `get_db` 真的把 Session 注入了。

## 8. 检查清单（学完自测）

- [ ] 能说出 `Depends()` 把「造对象」和「用对象」分开了。
- [ ] 能解释为什么全局共享一个 Session 会出线程安全问题。
- [ ] 能解释为什么 new 了不 close 会导致连接池耗尽（`QueuePool overflow`）。
- [ ] 知道 `get_db` 用 `yield` + `finally` 实现「每请求一个、用完即还」。
- [ ] 能写一个嵌套依赖（如 `require_admin` 依赖 `get_current_user`）。
- [ ] 知道怎么用 `app.dependency_overrides` 在测试里替换 `get_db`。

## 9. 下一步

- 把 `get_current_user` 换成真实 JWT 校验（引入 `python-jose` + `passlib`）。
- 给 `get_db` 加上异常时 `db.rollback()` 的兜底。
- 学 `BackgroundTasks`、`Request`、`Response` 这些内置依赖。
