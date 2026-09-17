from fastapi import FastAPI, Request
from .services import device_service
from .api import devices
from fastapi.responses import JSONResponse
from app.core.exceptions import DeviceNotFoundError

app = FastAPI(title="Atlas AI")
app.include_router(devices.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(request: Request, exc: DeviceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})
