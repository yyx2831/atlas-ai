"""所有 URL 在这里集中注册；backend 无 /api 前缀，代理负责去前缀。"""

from fastapi import FastAPI
from app.api.routes import (
    devices,
    protected,
    auth,
    knowledge,
    chat,
    agent,
    alarms,
    system,
)


def register_routes(app: FastAPI) -> None:
    for module in (system, auth, devices, alarms, protected, knowledge, chat, agent):
        app.include_router(module.router)
