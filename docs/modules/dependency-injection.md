# 模块：依赖注入（dependency-injection）

> 覆盖：`backend/app/dependencies.py`、`backend/app/database.py`（`get_db`）

## 为什么「Session 不该每个接口自己 new」

- 如果每个端点里 `db = Session()` 然后自己关，容易**忘记关闭**导致连接泄漏，也难做事务边界统一。
- FastAPI 的 `yield` 依赖会在**请求结束时**自动执行 `finally` 里的清理，把连接归还连接池——这正是 `get_db` 的做法。
- 同理，当前用户 `get_current_user` 也抽成依赖，端点签名只写 `user: CurrentUser`，逻辑与装配解耦，便于将来换成真实 JWT。

## 两个核心依赖

### `get_db`（每请求一个 Session）

```python
# app/database.py
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

端点用法：`db: Annotated[Session, Depends(get_db)]`。

### `get_current_user` / `require_admin`（当前用户）

```python
# app/dependencies.py
class User(BaseModel):
    id: int
    username: str
    is_active: bool = True
    is_admin: bool = False

FAKE_USER = User(id=1, username="yyx", is_active=True, is_admin=True)

def get_current_user(x_user_id: int | None = Header(default=None, alias="X-User-Id")) -> User:
    if x_user_id is None:
        return FAKE_USER
    return User(id=x_user_id, username=f"user-{x_user_id}", is_active=True)

def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
```

- `get_current_user` 现在**是假实现**：无 `X-User-Id` 头就返回写死的 `FAKE_USER`；有则假装是该用户。
- `require_admin` 是**嵌套依赖**：它自己又依赖 `get_current_user`，FastAPI 自动先解析内层再校验。

## 端点注入写法（推荐 `Annotated`）

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import User, get_current_user, require_admin

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/ping-db")
def ping_db(db: DbSession): ...

@router.get("/me")
def read_me(user: CurrentUser): ...

@router.get("/admin")
def read_admin(user: Annotated[User, Depends(require_admin)]): ...
```

## 注意事项

- **把 service 接上数据库时**，给 `device_service` 的 CRUD 函数加参数 `db: Session = Depends(get_db)`，在端点层传入 `db`（或在 service 内部 `Depends`，但 service 函数通常不自己声明 Depends，更常见是端点注入后传参）。
- `User` 模型当前放在 `dependencies.py`（教学自包含）；真实项目建议挪到 `schemas/user.py`。
- 真实鉴权路线（写在 `get_current_user` 注释里）：取 `Authorization` Bearer Token → jwt 解码/校验 → 用 `user_id` 查库 → 不存在/禁用则 401。

## 相关文档

- 数据库与 Session → `database-models.md`
- 路由如何使用这些依赖 → `routing.md`
- 一次请求的 DI 流转 → `../architecture/request-lifecycle.md`

## 2026-09-21 持久化接线

设备五个路由也注入 get_db。函数实际返回 Iterator[Session]，使用 with SessionLocal() 关闭资源；普通 service 显式接收 db，不把 Depends 当普通函数默认实参。
