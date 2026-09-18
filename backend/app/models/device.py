"""设备表 ORM 模型。

与 schemas/device.py 的 Pydantic 模型对应：
- schemas.DeviceCreate    -> 创建请求体
- schemas.DeviceResponse  -> 返回响应
- models.Device          -> 数据库表（这一张）
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
