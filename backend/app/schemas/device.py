from enum import Enum
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator

class DeviceType(str, Enum):
    router = "router"
    switch = "switch"
    camera = "camera"
@field_validator("name")
@classmethod
def name_not_blank(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("name 不能为空")
    return v.strip()

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, description="设备名称，不能为空")
    device_type: DeviceType
    ip: IPvAnyAddress

class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    device_type: DeviceType | None = None
    ip: IPvAnyAddress | None = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    device_type: DeviceType
    ip: str