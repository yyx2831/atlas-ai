from typing import Annotated
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.services import device_service

DbSession = Annotated[Session, Depends(get_db)]

from app.dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/devices",
    tags=["设备管理"],
    dependencies=[Depends(get_current_user)],  # 此路由下的所有接口都会触发 token 校验
)


@router.get("", response_model=list[DeviceResponse])
def list_devices(db: DbSession):
    return device_service.list_devices(db)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int, db: DbSession):
    device = device_service.get_device(device_id, db)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_device(data: DeviceCreate, db: DbSession):
    return device_service.create_device(data, db)


@router.put(
    "/{device_id}", response_model=DeviceResponse, dependencies=[Depends(require_admin)]
)
def update_device(device_id: int, data: DeviceUpdate, db: DbSession):
    device = device_service.update_device(device_id, data, db)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_device(device_id: int, db: DbSession):
    ok = device_service.delete_device(device_id, db)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不存在")
    return None
