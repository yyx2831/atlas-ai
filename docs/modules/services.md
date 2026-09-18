# 模块：业务逻辑层（services）

> 覆盖：`backend/app/services/device_service.py`、`backend/app/services/__init__.py`

## 职责

`services` 是业务逻辑层，路由层只调用它、不写业务。当前 `device_service` 是**内存版假数据**实现，用于演示分层，尚未接数据库。

## 当前实现（内存列表）

```python
from app.schemas.device import DeviceCreate, DeviceUpdate

_devices: list[dict] = []
_next_id = 1

def list_devices() -> list[dict]: ...
def get_device(device_id: int) -> dict | None: ...
def create_device(data: DeviceCreate) -> dict: ...
def update_device(device_id: int, data: DeviceUpdate) -> dict | None: ...
def delete_device(device_id: int) -> bool: ...

# 辅助函数（演示用，未被路由调用）
def calculate_total(prices: list[float]) -> float: ...
def group_devices(devices: list[dict]) -> dict[str, list[dict]]: ...
def filter_alarm_devices(devices: list[dict], level: str = "critical") -> list[dict]: ...
```

- `create_device` 用 `data.model_dump(mode="json")` 把 Pydantic 入参转 dict，再补 `id`。
- `update_device` 用 `exclude_unset=True, exclude_none=True` 做局部更新。
- `services/__init__.py` 把 5 个 CRUD 函数聚合导出，供 `routes/devices.py` 调用。

## 待办（下一步最自然的改造）

把内存版改成数据库版，打通 `routes → schemas → services → models → DB` 全链路：

```python
# 目标形态（伪代码）
from sqlalchemy.orm import Session
from app.models import Device

def list_devices(db: Session) -> list[Device]:
    return db.query(Device).all()

def create_device(data: DeviceCreate, db: Session) -> Device:
    device = Device(**data.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device
# ... 其余同理
```

调用方（`routes/devices.py`）把注入的 `db` 传进来即可：

```python
from app.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@router.get("", response_model=list[DeviceResponse])
def list_devices(db: Annotated[Session, Depends(get_db)]):
    return device_service.list_devices(db)
```

> 注意：`DeviceResponse` 的 `ip` 字段类型是 `str`，而 `DeviceCreate.ip` 是 `IPvAnyAddress`；从 ORM 对象序列化时 `ip` 已是字符串，匹配无碍。

## 注意事项

- service 函数**当前没有** `db` 参数；加 DB 支持时记得同步改路由调用签名。
- `calculate_total` / `group_devices` / `filter_alarm_devices` 是早期演示辅助函数，当前无路由使用；保留可作练习或删除。
- 保持「路由薄、service 厚」：新业务逻辑放这里，不要在路由里写。

## 相关文档

- 数据库与 ORM → `database-models.md`
- 依赖注入（`get_db`）→ `dependency-injection.md`
- 路由如何调用 → `routing.md`
