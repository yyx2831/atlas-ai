"""Day 16/19：设备一对多告警。"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base

if TYPE_CHECKING:
    from app.models.device import Device


class Alarm(Base):
    __tablename__ = "alarms"
    __table_args__ = (Index("ix_alarms_device_created", "device_id", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    device: Mapped["Device"] = relationship(back_populates="alarms")
