"""应用入口：只负责“装配” FastAPI 应用。

具体逻辑已抽离到独立模块，保持单一职责：
- app.core.config              应用元数据配置
- app.core.logging_config     日志与 request_id 上下文
- app.core.middleware          请求级中间件（含中间件测试）
- app.core.exception_handlers 异常处理器
- app.api.router.register_routes 路由聚合挂载

关键修复：原 main.py 末尾的“# ========== 中间件测试 ==========”片段里误写了
`app = FastAPI(title="Middleware Demo")`，重新创建了一个 FastAPI 实例，
把前面已挂载的全部路由 / 中间件 / 异常处理器全部覆盖掉了，导致 /docs 只剩
该片段里的 GET /devices 和 GET /。本版本不再重建 app，中间件统一注册到
“同一个” app 实例上，所有路由都能正确注册并显示在 /docs。
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db

from app.api.router import register_routes
from app.core.config import DESCRIPTION, TITLE, VERSION
from app.core.exception_handlers import device_not_found_handler, global_exception_handler
from app.core.exceptions import DeviceNotFoundError
from app.core.middleware import add_request_id, request_timing_middleware

# 1) 创建应用（全工程只此一处）
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 仅教学建表；create_all 不负责已有字段升级，Day 20 再使用 Alembic。
    init_db()
    yield


app = FastAPI(title=TITLE, description=DESCRIPTION, version=VERSION, lifespan=lifespan)

# 2) 注册路由（尽早执行，确保即使后续中间件 / 处理器有问题，路由也已挂载）
register_routes(app)

# 3) 注册中间件
# 请求 id 注入（内层，紧贴端点）
app.middleware("http")(add_request_id)

# ========== 中间件测试 ==========
# 测试用中间件：统计请求耗时并打印，验证中间件链正常。
# 注册到“同一个 app 实例”，绝不再写 app = FastAPI(...) 覆盖应用。
app.middleware("http")(request_timing_middleware)

# 4) 注册异常处理器
app.add_exception_handler(DeviceNotFoundError, device_not_found_handler)
app.add_exception_handler(Exception, global_exception_handler)
