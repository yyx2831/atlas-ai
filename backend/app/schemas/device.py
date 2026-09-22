from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, field_validator


class DeviceType(str, Enum):
    router = "router"
    switch = "switch"
    camera = "camera"


class DeviceNameValidation(BaseModel):
    @field_validator("name", check_fields=False)
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None  # 保留现有更新接口 null=忽略 的语义
        value = value.strip()
        if not value:
            raise ValueError("name 不能为空")
        return value


class DeviceCreate(DeviceNameValidation):
    name: str = Field(min_length=1, max_length=100, description="设备名称")
    device_type: DeviceType
    ip: IPvAnyAddress


class DeviceUpdate(DeviceNameValidation):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    device_type: DeviceType | None = None
    ip: IPvAnyAddress | None = None


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    device_type: DeviceType
    ip: str
