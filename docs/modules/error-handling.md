# 模块：异常处理（error-handling）

> 覆盖：`backend/app/core/exception_handlers.py`、`backend/app/core/exceptions.py`

## 职责

- `exceptions.py`：自定义业务异常 `DeviceNotFoundError`。
- `exception_handlers.py`：两个处理器——`device_not_found_handler`（专用 404）、`global_exception_handler`（兜底所有 `Exception`）。

## exceptions.py

```python
class DeviceNotFoundError(Exception):
    """设备不存在"""
    pass
```

> 注意：`routes/devices.py` 当前并**没有**抛 `DeviceNotFoundError`，而是直接 `raise HTTPException(404, "设备不存在")`。`device_not_found_handler` 已注册但暂时无触发路径——保留作未来 service 抛自定义异常的接入口。

## exception_handlers.py

```python
async def device_not_found_handler(request, exc: DeviceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

async def global_exception_handler(request, exc: Exception):
    request_id = getattr(request.state, "request_id", "")
    token = request_id_var.set(request_id)          # 临时 set，让本处理器日志也带 id
    try:
        logger.error("未处理异常已统一捕获", exc_info=exc)
    finally:
        request_id_var.reset(token)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误", "request_id": request_id})
```

## 注册（main.py）

```python
app.add_exception_handler(DeviceNotFoundError, device_not_found_handler)
app.add_exception_handler(Exception, global_exception_handler)
```

## 异常如何被处理（优先级）

| 异常类型 | 谁处理 | 返回 |
|---|---|---|
| `DeviceNotFoundError` | 专用 `device_not_found_handler` | 404 JSON |
| `HTTPException`（404/422/502/504 等） | Starlette 默认处理器 | 对应状态码 JSON |
| 其它未捕获异常（如 `ZeroDivisionError`） | `global_exception_handler` | **500 JSON**，带 request_id |

## 为什么不再有原生 ASGI 堆栈

`/log-error` 故意 `1/0` 并 `raise e` 后，异常一路冒泡，被 `global_exception_handler` 接住并返回 500 JSON——**因为被接住，uvicorn 不再打印 `Exception in ASGI application` 那一大串原生追踪栈**。控制台只剩你定义的格式化日志（`业务发生除零异常` + `未处理异常已统一捕获`）。

## 注意事项

- **生产建议**：捕获裸 `Exception` 过于宽泛，可能吞掉不该吞的错误（如 `KeyboardInterrupt` 之外的系统信号）。更稳妥是只捕获自定义业务异常基类；测试环境这样写没问题。
- 全局处理器的 `request_id` 来自 `request.state`（因为 `add_request_id` 的 `finally` 已 reset contextvar），并临时 `set` 保证本处理器日志带 id。
- `HTTPException` 不会进 `global_exception_handler`（Starlette 在其前拦截）。

## 相关文档

- 中间件/日志（request_id 来源）→ `middleware-logging.md`
- 请求生命周期（异常分支）→ `../architecture/request-lifecycle.md`
- 路由如何抛错 → `routing.md`
