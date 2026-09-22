from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from app.dependencies import CurrentUser, DbSession
from app.models import Device
from app.models.platform import AgentRun
from app.schemas.platform import AgentInput
from app.services.agent import run_agent

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/runs", status_code=201)
async def run(data: AgentInput, request: Request, db: DbSession, user: CurrentUser):
    if db.get(Device, data.device_id) is None:
        raise HTTPException(404, "设备不存在")
    row = AgentRun(owner_id=user.id, question=data.question)
    db.add(row)
    db.commit()
    try:
        token = (
            request.headers.get("authorization", "")
            .removeprefix("Bearer ")
            .removeprefix("bearer ")
        )
        result = await run_agent(db, request.app.state.runtime, user.id, data, token)
        row.answer = result["answer"]
        row.steps = result["steps"]
        row.status = "completed"
        db.commit()
    except BaseException:
        db.rollback()
        row.status = "failed"
        db.commit()
        raise
    return {
        "id": row.id,
        "status": row.status,
        "answer": row.answer,
        "steps": row.steps,
    }


@router.get("/runs")
def runs(db: DbSession, user: CurrentUser):
    return [
        {
            "id": r.id,
            "question": r.question,
            "status": r.status,
            "answer": r.answer,
            "steps": r.steps,
        }
        for r in db.scalars(
            select(AgentRun)
            .where(AgentRun.owner_id == user.id)
            .order_by(AgentRun.created_at.desc())
            .limit(30)
        )
    ]
