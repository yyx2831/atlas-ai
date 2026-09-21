"""SQLAlchemy ORM 模型包。

所有数据库表模型都继承这里的 Base。
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.device import Device  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
from app.models.alarm import Alarm  # noqa: E402,F401

__all__ = ["Base", "Device", "User", "Alarm"]
