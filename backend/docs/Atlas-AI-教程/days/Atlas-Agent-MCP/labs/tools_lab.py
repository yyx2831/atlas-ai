"""Day 17/19：教学数据与工具。完全离线，不读写 Atlas 数据库。"""

import json
from pydantic import BaseModel, ConfigDict, Field

DEVICES = {1: {"id": 1, "name": "Router-A", "ip": "192.0.2.10"}}
ALARMS = [
    {
        "id": 2,
        "device_id": 1,
        "level": "critical",
        "created_at": "2026-09-20T10:00:00Z",
    },
    {"id": 1, "device_id": 1, "level": "warning", "created_at": "2026-09-20T09:00:00Z"},
]
MANUAL = {
    "document_id": "manual-demo",
    "filename": "router-manual.md",
    "page": 1,
    "content": "ERR-1007 表示链路不稳定。断连时检查网线、端口与供电；告警本身不能证明根因。",
}


def get_device(device_id: int) -> dict:
    if device_id not in DEVICES:
        raise ValueError("设备不存在")
    return {**DEVICES[device_id], "note": "虚构登记信息，不是实时状态"}


def get_alarm(device_id: int, limit: int = 10) -> list[dict]:
    get_device(device_id)
    return [a.copy() for a in ALARMS if a["device_id"] == device_id][:limit]


def search_manual(query: str) -> list[dict]:
    # 这里只演示工具的输入/输出形状，不是 RAG 检索算法。
    return (
        [MANUAL.copy()]
        if any(word in query for word in ("断连", "ERR-1007", "网线"))
        else []
    )


class DeviceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: int = Field(gt=0, strict=True)


class AlarmInput(DeviceInput):
    limit: int = Field(default=10, ge=1, le=30, strict=True)


class ManualInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2000)


MODELS = {
    "get_device": DeviceInput,
    "get_alarm": AlarmInput,
    "search_manual": ManualInput,
}
FUNCTIONS = {
    "get_device": get_device,
    "get_alarm": get_alarm,
    "search_manual": search_manual,
}
DESCRIPTIONS = {
    "get_device": "查询设备登记信息，不是实时状态",
    "get_alarm": "查询设备近期告警",
    "search_manual": "根据问题检索维修手册，返回原文、文件名和页码",
}


def schemas(names):
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": DESCRIPTIONS[name],
                "parameters": MODELS[name].model_json_schema(),
            },
        }
        for name in names
    ]


def validate_call(name: str, raw_arguments: str, selected_device: int) -> dict:
    if name not in MODELS:
        raise ValueError("未知工具")
    values = MODELS[name].model_validate(json.loads(raw_arguments)).model_dump()
    if values.get("device_id", selected_device) != selected_device:
        raise ValueError("不允许更换本次选择的设备")
    return values


async def execute(name: str, values: dict):
    # 教学数据在内存，瞬间返回。真实 HTTP 工具才需要 await 网络请求。
    return FUNCTIONS[name](**values)
