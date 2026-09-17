from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.services.device_service import get_device
from app.core.exceptions import DeviceNotFoundError
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.services import device_service

# 路由级依赖函数：校验请求头 Token
def verify_device_token(x_device_token: str = Header("default-token")):
    if x_device_token != "secret-device-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Device Token"
        )

router = APIRouter(
    prefix="/devices",
    tags=["设备管理"],
    dependencies=[Depends(verify_device_token)]  # 此路由下的所有接口都会触发 token 校验
)
@router.get("", response_model=list[DeviceResponse])
def list_devices():
    return device_service.list_devices()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int):
    device = device_service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(data: DeviceCreate):
    return device_service.create_device(data)


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, data: DeviceUpdate):
    device = device_service.update_device(device_id, data)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int):
    ok = device_service.delete_device(device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不存在")
    return None