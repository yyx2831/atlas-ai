import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.dependencies import DbSession, CurrentUser

router = APIRouter(tags=["运行状态"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request, db: DbSession):
    try:
        db.execute(text("SELECT 1"))
        runtime = request.app.state.runtime
        await asyncio.to_thread(
            runtime.vectors.client.get_collection, runtime.vectors.collection
        )
        if runtime.limiter.redis:
            await asyncio.to_thread(runtime.limiter.redis.ping)
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@router.get("/system/info")
def info(request: Request, user: CurrentUser):
    runtime = request.app.state.runtime
    s = runtime.settings
    return {
        "llm_mode": s.llm_mode,
        "model": s.llm_model if s.llm_mode != "demo" else "确定性演示",
        "embedding_mode": s.embedding_mode,
        "reranker": s.rerank_model or "未启用（RRF 排名融合）",
        "vector_store": "Qdrant server" if s.qdrant_url else "Qdrant local",
        "index_key": runtime.vectors.collection,
        "max_upload_mb": s.max_upload_bytes // 1024 // 1024,
    }
