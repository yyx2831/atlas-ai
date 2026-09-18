# 模块：HTTP 路由层（routing）

> 覆盖：`backend/app/api/routes/*.py`、`backend/app/api/router.py`、`backend/app/api/routes/__init__.py`

## 路由分组（按 tag，全部根级、无 `/api` 前缀）

| tag | 文件 | prefix | 端点 | 守卫 |
|---|---|---|---|---|
| 系统运维 | `health.py` | `/health` | `GET /health` | 无 |
| 用户管理 | `users.py` | `/users` | `GET /users`、`GET /users/{id}` | 无（假数据） |
| 设备管理 | `devices.py` | `/devices` | `GET /devices`、`GET /devices/{id}`、`POST /devices`、`PUT /devices/{id}`、`DELETE /devices/{id}` | 路由级 `X-Device-Token` 必须 `= secret-device-key` |
| 当前用户（演示 DI） | `protected.py` | `/me` | `GET /me`、`GET /me/admin`、`GET /me/ping-db` | 依赖注入 `get_current_user` / `require_admin` / `get_db` |
| 演示 / 实验 | `demo.py` | 无 | `GET /`（隐藏）、`GET /external/test`、`GET /log-test`、`GET /log-error` | 无 |

合计 **11 组接口**，全部出现在 `/docs`（OpenAPI）。

## 关键实现点

### devices.py —— 路由级依赖做 token 守卫

```python
def verify_device_token(x_device_token: str = Header("default-token")):
    if x_device_token != "secret-device-key":
        raise HTTPException(status_code=401, detail="Invalid Device Token")

router = APIRouter(
    prefix="/devices",
    tags=["设备管理"],
    dependencies=[Depends(verify_device_token)],   # 整组接口统一校验
)
```

> 注意：路由里 `from app.services import device_service` 与 `from app.services.device_service import get_device` 混用，功能正常但略冗余；统一用 `device_service.xxx` 即可。

### protected.py —— `Annotated` 注入（推荐写法）

```python
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("")            # GET /me
def read_me(user: CurrentUser): ...

@router.get("/admin")      # GET /me/admin
def read_admin(user: Annotated[User, Depends(require_admin)]): ...

@router.get("/ping-db")    # GET /me/ping-db
def ping_db(db: DbSession): ...
```

### demo.py —— 外部调用 + 日志实验

- `GET /external/test`：`call_external_api()` 用 httpx 异步请求 `https://httpbin.org/delay/3`（故意延迟 3s），超时 2s，tenacity 重试 2 次（仅 `httpx.TimeoutException`）；最终 504/502。
- `GET /log-test`：打 INFO/WARNING/ERROR 三条日志，返回 request_id。
- `GET /log-error`：故意 `1/0` → 打业务日志 → `raise e`，演示全局异常处理器（见 `error-handling.md`）。

## 注意事项

- **新增端点**：在对应 `routes/*.py` 加 `@router.get/post/...`，在 `__init__.py` 聚合，在 `router.py` 挂载（见 `entrypoint.md`）。
- 路由不要写重业务逻辑——转调 `services`。
- `POST /devices` 的 `device_type` 必须是枚举 `router/switch/camera`，`ip` 必须是合法 IP，否则 422（见 `database-models.md` 的 schema 校验）。

## 相关文档

- 入口装配 → `entrypoint.md`
- 依赖注入 → `dependency-injection.md`
- 业务层 → `services.md`
- 数据校验 → `database-models.md`
