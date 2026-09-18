# 模块：中间件与日志（middleware-logging）

> 覆盖：`backend/app/core/middleware.py`、`backend/app/core/logging_config.py`

## 职责

- `logging_config.py`：集中定义全局 `logger`、`RequestIdFilter`、`request_id_var`，并一次性配置 root logger（防重复添加）。
- `middleware.py`：两个 HTTP 中间件——`add_request_id`（注入 request_id）、`request_timing_middleware`（统计耗时打印）。

## logging_config.py

```python
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

if not logging.getLogger().handlers:          # 仅当无 handler 时配置，避免重复
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, ...)

logger = logging.getLogger("app")
if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
    logger.addFilter(RequestIdFilter())
```

- 日志格式：`时间 | 级别 | request_id | 模块 | 消息`（见 `LOG_FORMAT`）。
- **禁止 `print()`**，统一用 `logger`。

## middleware.py

```python
async def add_request_id(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id           # 稳定来源（供异常处理器读）
    token = request_id_var.set(request_id)          # 供日志 Filter 读
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        raise exc                                   # 不在此打堆栈，交给全局处理器
    finally:
        request_id_var.reset(token)

async def request_timing_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000)
    req_id = getattr(request.state, "request_id", "") or request_id_var.get()
    logger.info(f"{request.method} {request.url.path} {response.status_code} {duration_ms}ms request_id={req_id}")
    return response
```

## 注册方式（务必用同一个 app 实例）

在 `main.py`：

```python
app.middleware("http")(add_request_id)
app.middleware("http")(request_timing_middleware)
```

> 历史 bug：曾误在中间件片段里写 `app = FastAPI(...)` 重新建实例，覆盖路由（见 `entrypoint.md`）。

## 注意事项

- **`request_id` 的两种来源**：`request.state`（同步端点经线程池执行时 contextvar 可能丢失，故优先 `state`）+ `request_id_var`（异步正常）。`request_timing_middleware` 用 `state or var` 兜底，保证日志稳定带 id。
- `add_request_id` 的 `finally: request_id_var.reset(token)` 会在**端点返回后、全局异常处理器执行前**重置 contextvar——所以全局处理器从 `request.state.request_id` 读，并临时 `set` 一次让自身日志也带 id（见 `error-handling.md`）。
- 中间件**不捕获异常打堆栈**：异常上抛给全局异常处理器统一记录，避免重复日志。

## 相关文档

- 入口装配（注册位置）→ `entrypoint.md`
- 异常处理（谁接住异常）→ `error-handling.md`
- 请求流转 → `../architecture/request-lifecycle.md`
