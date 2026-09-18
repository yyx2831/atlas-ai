"""演示 / 实验路由：根路由、外部接口调用、日志测试。

这些原本内联在 main.py，现抽离为独立 router，保持 main.py 精简。
"""
import httpx
from fastapi import APIRouter, HTTPException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.logging_config import logger, request_id_var

router = APIRouter(tags=["演示 / 实验"])


@router.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to Atlas AI API. Visit /docs for OpenAPI documentation."}


# ========== 外部接口调用（httpx + tenacity 重试） ==========
@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(0.5),
    retry=retry_if_exception_type(httpx.TimeoutException),
)
async def call_external_api() -> dict:
    timeout = httpx.Timeout(2.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 该接口故意延迟 3 秒返回，用于测试超时与重试
        resp = await client.get("https://httpbin.org/delay/3")
        resp.raise_for_status()
        return resp.json()


@router.get("/external/test")
async def external_test():
    try:
        data = await call_external_api()
        return {"msg": "调用外部接口成功", "external_data": data}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="外部接口调用超时，重试后依然失败")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"外部接口错误码：{e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"网络异常：{str(e)}")


# ========== 日志测试接口 ==========
@router.get("/log-test")
def log_test():
    logger.info("这是 INFO 日志：正常业务消息")
    logger.warning("这是 WARNING 日志：警告，非阻断")
    logger.error("这是 ERROR 日志：发生错误")
    return {"msg": "查看控制台日志", "request_id": request_id_var.get()}


@router.get("/log-error")
def log_error_demo():
    try:
        1 / 0
    except Exception as e:
        logger.error("业务发生除零异常", exc_info=True)
        raise e
