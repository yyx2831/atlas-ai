"""HTTP 输入模型：长度、范围与枚举在进入业务层之前验证。"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AccountInput(LoginInput):
    password: str = Field(min_length=12, max_length=128)
    role: Literal["admin", "viewer"] = "viewer"


class ChatInput(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None
    use_knowledge: bool = True
    top_k: int = Field(default=5, ge=1, le=10)
    product: str = Field(default="", max_length=80)
    version: str = Field(default="", max_length=80)


class AgentInput(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    device_id: int = Field(gt=0)
    engine: Literal["loop", "graph"] = "loop"
    transport: Literal["local", "mcp"] = "local"


class AlarmInput(BaseModel):
    level: Literal["info", "warning", "critical"]


class DeviceToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: int = Field(gt=0, strict=True)


class AlarmToolInput(DeviceToolInput):
    limit: int = Field(default=10, ge=1, le=30)


class ManualToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2000)
