import asyncio
import json
from time import perf_counter
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from app.dependencies import CurrentUser, DbSession
from app.models.platform import Conversation, Message
from app.schemas.platform import ChatInput
from app.services import chat as service
from app.services.llm import ProviderError

router = APIRouter(tags=["聊天与历史"])


@router.get("/conversations")
def conversations(db: DbSession, user: CurrentUser):
    return [
        {"id": c.id, "title": c.title, "created_at": c.created_at}
        for c in db.scalars(
            select(Conversation)
            .where(Conversation.owner_id == user.id)
            .order_by(Conversation.created_at.desc())
        )
    ]


@router.get("/conversations/{identifier}")
def history(identifier: str, db: DbSession, user: CurrentUser):
    service.conversation_for(db, user.id, identifier)
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == identifier)
        .order_by(Message.id)
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "status": m.status,
            "citations": m.citations,
            "metrics": m.metrics,
        }
        for m in rows
    ]


@router.delete("/conversations/{identifier}", status_code=204)
def remove(identifier: str, db: DbSession, user: CurrentUser):
    conversation = service.conversation_for(db, user.id, identifier)
    if db.scalar(
        select(Message.id).where(
            Message.conversation_id == identifier, Message.status == "pending"
        )
    ):
        raise HTTPException(409, "请等待生成结束后再删除会话")
    db.execute(delete(Message).where(Message.conversation_id == identifier))
    db.delete(conversation)
    db.commit()


@router.post("/chat")
async def chat(data: ChatInput, request: Request, db: DbSession, user: CurrentUser):
    runtime = request.app.state.runtime
    start = perf_counter()
    identifier, message_id, messages, sources = await service.prepare(
        db, runtime, user.id, data
    )
    try:
        if data.use_knowledge and not sources:
            answer = "当前知识库没有足够资料。请上传相关手册，或调整产品和版本筛选。"
        else:
            async with asyncio.timeout(runtime.settings.llm_timeout + 5):
                answer = (await runtime.llm.complete(messages)).get("content") or ""
        answer, citations = service.validate_citations(answer, sources)
        metrics = {
            "latency_ms": round((perf_counter() - start) * 1000),
            "mode": runtime.settings.llm_mode,
        }
        service.save_answer(
            db.get_bind(), message_id, answer, "completed", citations, metrics
        )
        return {
            "conversation_id": identifier,
            "answer": answer,
            "citations": citations,
            "metrics": metrics,
        }
    except BaseException:
        service.save_answer(db.get_bind(), message_id, "", "failed", [], {})
        raise


@router.post("/chat/stream")
async def stream(data: ChatInput, request: Request, db: DbSession, user: CurrentUser):
    runtime = request.app.state.runtime
    start = perf_counter()
    identifier, message_id, messages, sources = await service.prepare(
        db, runtime, user.id, data
    )
    bind = db.get_bind()

    def event(name, payload):
        return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def events():
        answer = ""
        status = "cancelled"
        citations = []
        metrics = {"mode": runtime.settings.llm_mode, "usage": None, "ttft_ms": None}
        try:
            yield event(
                "meta",
                {
                    "conversation_id": identifier,
                    "message_id": message_id,
                    "mode": runtime.settings.llm_mode,
                },
            )
            if data.use_knowledge and not sources:
                answer = "当前知识库没有足够资料。请上传相关手册，或调整筛选条件。"
                yield event("delta", {"text": answer})
            else:
                async with asyncio.timeout(runtime.settings.llm_timeout + 5):
                    async for part in runtime.llm.stream(messages):
                        if await request.is_disconnected():
                            return
                        if part["type"] == "delta":
                            if metrics["ttft_ms"] is None:
                                metrics["ttft_ms"] = round(
                                    (perf_counter() - start) * 1000
                                )
                            answer += part["text"]
                            if len(answer) > 50000:
                                raise ProviderError("回答超过长度限制")
                            yield event("delta", {"text": part["text"]})
                        elif part["type"] == "usage":
                            metrics["usage"] = part["usage"]
            answer, citations = service.validate_citations(answer, sources)
            status = "completed"
            metrics["latency_ms"] = round((perf_counter() - start) * 1000)
            service.save_answer(bind, message_id, answer, status, citations, metrics)
            yield event(
                "done", {"answer": answer, "citations": citations, "metrics": metrics}
            )
        except (ProviderError, TimeoutError) as exc:
            status = "failed"
            yield event("error", {"detail": str(exc) or "请求超时"})
        finally:
            metrics["latency_ms"] = round((perf_counter() - start) * 1000)
            service.save_answer(bind, message_id, answer, status, citations, metrics)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
