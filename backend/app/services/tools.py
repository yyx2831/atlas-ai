"""Agent 的工具白名单。无 eval、任意 SQL、Shell 或真实设备写操作。"""

import json
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Device, Alarm
from app.schemas.platform import DeviceToolInput, AlarmToolInput, ManualToolInput
from app.services.knowledge import search

TOOL_MODELS = {
    "get_device": DeviceToolInput,
    "get_alarm": AlarmToolInput,
    "search_manual": ManualToolInput,
}
TOOL_DESCRIPTIONS = {
    "get_device": "查询指定设备的登记信息（不代表实时在线状态）",
    "get_alarm": "查询设备最近告警，按时间倒序",
    "search_manual": "检索当前用户有权访问的维修手册，返回正文和来源页码",
}
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": TOOL_DESCRIPTIONS[name],
            "parameters": model.model_json_schema(),
        },
    }
    for name, model in TOOL_MODELS.items()
]


def validate_call(name: str, arguments: str, device_id: int) -> dict:
    if name not in TOOL_MODELS:
        raise ValueError("工具不在白名单中")
    data = TOOL_MODELS[name].model_validate(json.loads(arguments))
    values = data.model_dump()
    if values.get("device_id", device_id) != device_id:
        raise ValueError("模型不可更换本次任务选择的设备")
    return values


async def execute_local(name: str, arguments: dict, db, runtime, owner_id: int):
    if name == "search_manual":
        return await search(db, runtime, owner_id, arguments["query"], 5)
    device = db.get(Device, arguments["device_id"])
    if device is None:
        raise HTTPException(404, "设备不存在")
    if name == "get_device":
        return {
            "id": device.id,
            "name": device.name,
            "device_type": device.device_type,
            "ip": device.ip,
            "note": "登记信息；未连接实时设备状态系统",
        }
    rows = db.scalars(
        select(Alarm)
        .where(Alarm.device_id == device.id)
        .order_by(Alarm.created_at.desc())
        .limit(arguments.get("limit", 10))
    )
    return [
        {"id": a.id, "level": a.level, "created_at": a.created_at.isoformat()}
        for a in rows
    ]
