# 请求生命周期（request-lifecycle）

> 以一个真实请求 `GET /me` 为例，串起中间件、路由、依赖注入、异常处理的完整链路。
> 其余端点（`/devices`、`/health`、`/external/test` 等）链路相同，差异只在端点逻辑与注入的依赖。

## 阶段 1：进入中间件链

请求到达 uvicorn → Starlette 按注册顺序执行 `@app.middleware("http")`：

1. **`add_request_id`**（`core/middleware.py`）
   - 从请求头 `X-Request-ID` 取 id，没有就 `uuid.uuid4()` 生成。
   - 同时写入两处：`request.state.request_id`（稳定，供异常处理器读）和 `request_id_var` contextvar（供日志 `RequestIdFilter` 读）。
   - `token = request_id_var.set(request_id)` → `await call_next(request)` → `finally: request_id_var.reset(token)`。
2. **`request_timing_middleware`**（`core/middleware.py`）
   - `start = perf_counter()` → `await call_next` → 计算 `duration_ms`。
   - 用 `request.state.request_id or request_id_var.get()` 取 id，打印 `METHOD PATH STATUS ms request_id=...`（统一 `logger`）。
   - 同步端点经线程池时 contextvar 可能为空，故优先 `request.state`。

> 注意：中间件**不捕获异常打堆栈**——异常统一上抛给全局异常处理器。

## 阶段 2：路由匹配与依赖解析

Starlette 把请求交给匹配的路由。`/me` 由 `api/routes/protected.py` 的 `router`（prefix=`/me`）处理：

```python
@router.get("")                       # 实际路径 GET /me
def read_me(user: CurrentUser):       # CurrentUser = Annotated[User, Depends(get_current_user)]
    return user
```

FastAPI 在调用 `read_me` 前，先解析其依赖 `get_current_user`：

- `get_current_user` 读请求头 `X-User-Id`；没有则返回 `FAKE_USER`（`User(id=1, username="yyx", is_admin=True)`）。
- 结果注入 `user` 参数。

若端点是 `GET /me/admin`，依赖链更长：`require_admin` 又依赖 `get_current_user`（嵌套依赖），FastAPI 自动先解析内层再执行外层校验。

若端点是 `GET /me/ping-db`，注入的是 `get_db` 提供的 SQLAlchemy `Session`（见 `modules/database-models.md`）。

## 阶段 3：端点执行（业务逻辑）

- `/me`：直接返回 `user` 字典（序列化由 FastAPI + Pydantic 完成）。
- `/devices`：端点无业务逻辑，转调 `device_service.list_devices()` 等；service 当前返回内存 `_devices` 列表。
- `/external/test`：异步调用 `call_external_api()`（httpx + tenacity 重试），再包装成 JSON 返回。
- `/log-error`：故意 `1/0` → 进入 `except` → `logger.error("业务发生除零异常", exc_info=True)` → **`raise e` 继续上抛**。

## 阶段 4：响应返回（再走中间件）

端点返回 → 控制权回到 `request_timing_middleware` 的 `call_next` 之后 → 打印耗时日志 → 回到 `add_request_id` 的 `call_next` 之后 → 把 `X-Request-ID` 写回响应头 → 响应发回客户端。

## 阶段 5：异常分支（若端点抛异常）

`/log-error` 的 `raise e` 冒泡：
1. 穿过 `request_timing_middleware`（其 `call_next` 抛出）→ 穿过 `add_request_id`（其 `call_next` 抛出，`except` 里只 `raise exc`，不打堆栈）。
2. **未被任何路由级处理器接住** → 到达全局异常处理器 `global_exception_handler`（`core/exception_handlers.py`，注册在 `main.py` 的 `app.add_exception_handler(Exception, ...)`）。
3. 全局处理器：
   - 从 `request.state.request_id` 取 id；临时 `request_id_var.set(id)` 让本处理器日志也带 id。
   - `logger.error("未处理异常已统一捕获", exc_info=exc)`（带 request_id 的格式化日志）。
   - 返回 `JSONResponse(500, {"detail": "服务器内部错误", "request_id": id})`。
4. **因为被全局处理器接住，uvicorn 不再打印原生 `Exception in ASGI application` 堆栈。**

> `DeviceNotFoundError` 走专用 `device_not_found_handler`（返回 404）；`HTTPException`（404/422/502/504）由 Starlette 默认处理器接管，不经过全局 `Exception` 处理器。

## 全链路图示

```
客户端
  │  GET /me  (Header: X-User-Id 可选)
  ▼
uvicorn ─ Starlette
  ▼
add_request_id        ── 写入 request_id (state + contextvar)
  ▼
request_timing_middleware ── 计时开始
  ▼
路由匹配 /me (protected.router)
  ▼
解析依赖 get_current_user ── 返回 user (或 FAKE_USER)
  ▼
端点 read_me(user) ── 返回 user 对象
  ▼
request_timing_middleware ── 打印耗时日志
  ▼
add_request_id ── 回写 X-Request-ID 响应头
  ▼
客户端  ← 200 {id, username, is_active, is_admin}

（异常时：raise → 全局 global_exception_handler → 500 JSON，无原生堆栈）
```

## 相关文档

- 依赖注入细节 → `../modules/dependency-injection.md`
- 中间件与日志 → `../modules/middleware-logging.md`
- 异常处理 → `../modules/error-handling.md`
- 路由总表 → `../modules/routing.md`
