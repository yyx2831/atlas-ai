"""Day 21：service 显式接收 Session；每个写操作拥有一个事务。"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Device
from app.schemas.device import DeviceCreate, DeviceUpdate


def calculate_total(prices: list[float]) -> float:
    return sum(prices)


def group_devices(devices: list[dict]) -> dict[str, list[dict]]:
    groups = {}
    for device in devices:
        group_name = device["group"]
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(device)
    return groups


def filter_alarm_devices(devices: list[dict], level: str = "critical") -> list[dict]:
    return [device for device in devices if device.get("level") == level]


def list_devices(db: Session) -> list[Device]:
    return list(db.scalars(select(Device).order_by(Device.id)))


def get_device(device_id: int, db: Session) -> Device | None:
    return db.get(Device, device_id)


def create_device(data: DeviceCreate, db: Session) -> Device:
    # json 模式将 IP 对象、枚举转为可保存的字符串。
    device = Device(**data.model_dump(mode="json"))
    try:
        db.add(device)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(device)
    return device


def update_device(device_id: int, data: DeviceUpdate, db: Session) -> Device | None:
    device = db.get(Device, device_id)
    if device is None:
        return None
    values = data.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    try:
        for field, value in values.items():
            setattr(device, field, value)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(device)
    return device


def delete_device(device_id: int, db: Session) -> bool:
    device = db.get(Device, device_id)
    if device is None:
        return False
    try:
        db.delete(device)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True
