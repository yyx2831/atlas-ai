from fastapi import FastAPI, Request
from .services import device_service
from .api.routes import devices
from fastapi.responses import JSONResponse
from app.core.exceptions import DeviceNotFoundError
from app.api.routes import health_router, users_router, devices_router

app = FastAPI(
    title="Atlas AI API",
    description="模块化架构接口文档",
    version="1.0.0"
)
app.include_router(devices.router)
# 集中挂载子路由
app.include_router(health_router)
app.include_router(users_router)
app.include_router(devices_router)
@app.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to Atlas AI API. Visit /docs for OpenAPI documentation."}

@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(request: Request, exc: DeviceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})
