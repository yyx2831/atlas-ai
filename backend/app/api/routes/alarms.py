from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.dependencies import DbSession, CurrentUser, AdminUser
from app.models import Device, Alarm
from app.schemas.platform import AlarmInput

router = APIRouter(prefix="/devices", tags=["设备告警"])


@router.get("/{device_id}/alarms")
def get_alarms(
    device_id: int,
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(10, ge=1, le=30),
):
    if db.get(Device, device_id) is None:
        raise HTTPException(404, "设备不存在")
    rows = db.scalars(
        select(Alarm)
        .where(Alarm.device_id == device_id)
        .order_by(Alarm.created_at.desc(), Alarm.id.desc())
        .limit(limit)
    )
    return [
        {
            "id": row.id,
            "device_id": row.device_id,
            "level": row.level,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/{device_id}/alarms", status_code=201)
def add_alarm(device_id: int, data: AlarmInput, db: DbSession, user: AdminUser):
    if db.get(Device, device_id) is None:
        raise HTTPException(404, "设备不存在")
    alarm = Alarm(device_id=device_id, level=data.level)
    db.add(alarm)
    db.commit()
    return {
        "id": alarm.id,
        "level": alarm.level,
        "created_at": alarm.created_at.isoformat(),
    }
