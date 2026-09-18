"""路由聚合：把各业务 router 统一挂载到 app。

原本这些 include_router 散落在 main.py，现集中到这里，保持 main.py 只做“装配”。
"""
from fastapi import FastAPI

from app.api.routes import demo_router, devices_router, health_router, users_router
from app.api.routes import protected


def register_routes(app: FastAPI) -> None:
    """集中注册所有子路由。

    注意：devices 只注册一次（devices_router 来自 routes/__init__ 聚合），
    避免原来 main.py 中 devices.router 与 devices_router 重复 include。
    """
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(devices_router)
    app.include_router(protected.router)
    app.include_router(demo_router)
