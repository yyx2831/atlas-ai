# 模块：入口装配（entrypoint）

> 覆盖：`backend/app/main.py`、`backend/app/api/router.py`、`backend/app/core/config.py`

## 职责

`main.py` 是**全工程唯一创建 `FastAPI` 实例**的地方，只做「装配」，不含业务。装配顺序：

1. 创建 `app = FastAPI(title=TITLE, description=DESCRIPTION, version=VERSION)`（来自 `core/config.py`）。
2. `register_routes(app)` —— 尽早挂路由，确保后续中间件/处理器出问题也不影响路由注册。
3. 注册中间件：`app.middleware("http")(add_request_id)`、`app.middleware("http")(request_timing_middleware)`。
4. 注册异常处理器：`app.add_exception_handler(DeviceNotFoundError, device_not_found_handler)`、`app.add_exception_handler(Exception, global_exception_handler)`。

`core/config.py` 仅放 `TITLE` / `DESCRIPTION` / `VERSION` 三个常量。

## 关键代码

```python
# app/main.py（核心骨架）
app = FastAPI(title=TITLE, description=DESCRIPTION, version=VERSION)  # 全工程只此一处
register_routes(app)
app.middleware("http")(add_request_id)
app.middleware("http")(request_timing_middleware)
app.add_exception_handler(DeviceNotFoundError, device_not_found_handler)
app.add_exception_handler(Exception, global_exception_handler)
```

```python
# app/api/router.py
def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(devices_router)   # devices 只注册一次（聚合在 routes/__init__）
    app.include_router(protected.router)
    app.include_router(demo_router)
```

## 注意事项（重要）

- **绝不在任何地方再写 `app = FastAPI(...)`**。历史上 `main.py` 末尾的「中间件测试」片段误写了 `app = FastAPI(title="Middleware Demo")`，重建了一个实例，**覆盖了前面已挂载的全部路由/中间件/异常处理器**，导致 `/docs` 只剩该片段里的 `GET /devices` 和 `GET /`。现已修复：中间件统一 `app.middleware("http")(func)` 注册到同一个实例。
- 新增路由：在 `api/routes/` 下建/改 router，并在 `api/routes/__init__.py` 聚合导出，再到 `router.py` 的 `register_routes` 里 `include_router`。**不要**在 `main.py` 直接 `include_router`（保持装配集中）。
- `main.py` 顶部 docstring 已把这条坑写进代码注释，改代码前先读。

## 相关文档

- 路由总表 → `routing.md`
- 中间件/日志 → `middleware-logging.md`
- 异常处理 → `error-handling.md`
- 完整源码 → 根目录 `ATLAS_AI_项目描述文档.md`
