"""Atlas 唯一应用入口。阅读顺序：配置 → 资源生命周期 → 路由 → 中间件。"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.api.router import register_routes
from app.core.settings import get_settings
from app.core.exception_handlers import global_exception_handler
from app.core.middleware import add_request_id, request_timing_middleware
from app.database import init_db, SessionLocal
from app.services.runtime import Runtime
from app.services.accounts import bootstrap_admin
from app.services.llm import ProviderError
from sqlalchemy import update
from app.models.platform import Message, AgentRun


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 仅创建新表，不修改已有列。已有数据库不执行删表或自动重置。
    init_db()
    settings = get_settings()
    with SessionLocal() as db:
        # 单 worker 应用重启后，把上次中断的任务标为失败，允许用户重新提问。
        db.execute(
            update(Message).where(Message.status == "pending").values(status="failed")
        )
        db.execute(
            update(AgentRun).where(AgentRun.status == "running").values(status="failed")
        )
        db.commit()
        if settings.admin_email and settings.admin_password:
            bootstrap_admin(db, settings.admin_email, settings.admin_password)
    runtime = Runtime(settings)
    app.state.runtime = runtime
    try:
        yield
    finally:
        await runtime.close()


app = FastAPI(
    title="Atlas AI",
    description="设备故障 AI 助手：Chat / RAG / Agent / MCP",
    version="0.2.0",
    lifespan=lifespan,
)
register_routes(app)
# 后注册的中间件在外层，request_id 包住计时和所有业务日志。
app.middleware("http")(request_timing_middleware)
app.middleware("http")(add_request_id)
app.add_exception_handler(Exception, global_exception_handler)


@app.exception_handler(ProviderError)
async def provider_error(request, exc):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(TimeoutError)
async def timeout_error(request, exc):
    return JSONResponse(status_code=504, content={"detail": "请求达到时间上限，已停止"})
