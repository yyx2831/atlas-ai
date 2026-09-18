"""全局 / 专用异常处理器。"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DeviceNotFoundError
from app.core.logging_config import logger, request_id_var


async def device_not_found_handler(request: Request, exc: DeviceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def global_exception_handler(request: Request, exc: Exception):
    """兜底捕获所有未被更具体处理器拦截的异常（如 ZeroDivisionError）。

    - 统一返回 JSON 500（而不是把异常抛给 uvicorn）；
    - 用带 request_id 的日志格式记录堆栈；
    - 阻止 uvicorn 再打印那一长串原生 ASGI Traceback。
    注意：HTTPException(404/422/502/504) 由 Starlette 默认处理器接管，不受影响。
    """
    request_id = getattr(request.state, "request_id", "")
    # RequestIdFilter 从 request_id_var 读 request_id；中间件 finally 已 reset，
    # 这里临时再 set 一次，保证本处理器的日志也带正确的 request_id。
    token = request_id_var.set(request_id)
    try:
        logger.error("未处理异常已统一捕获", exc_info=exc)
    finally:
        request_id_var.reset(token)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "request_id": request_id},
    )
