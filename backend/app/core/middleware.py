"""HTTP 中间件：请求级横切逻辑集中在此。

原本这些 @app.middleware 写在 main.py，现抽离为独立函数，
在 main.py 里用 app.middleware("http")(func) 注册到“同一个” app 实例上。
"""
import time
import uuid

from fastapi import Request

from app.core.logging_config import logger, request_id_var


async def add_request_id(request: Request, call_next):
    """为每个请求生成/透传 request_id，并注入日志上下文。"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    # 同时存到 request.state：异常处理器在 finally(reset) 之后才执行，
    # 直接读 contextvar 会得到空值，从 request.state 读则稳定。
    request.state.request_id = request_id
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        # 不在中间件里重复打堆栈：异常交给全局异常处理器统一记录
        raise exc
    finally:
        request_id_var.reset(token)


async def request_timing_middleware(request: Request, call_next):
    """中间件测试：统计请求耗时并打印，验证中间件链正常工作。

    对应原 main.py “# ========== 中间件测试 ==========”片段中的
    request_timing_middleware。原片段误用了 `app = FastAPI(...)`
    重新创建实例，导致先前挂载的全部路由丢失——这里改为注册到同一个 app 上。
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000)
    # add_request_id 同时把 request_id 写入 request.state 与 request_id_var；
    # 同步端点经线程池执行时 contextvar 传递偶有不一致，这里两者取其一，保证日志稳定带 id。
    req_id = getattr(request.state, "request_id", "") or request_id_var.get()
    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {duration_ms}ms request_id={req_id}"
    )
    return response
