# 源码签名地图（repo-map）

> 本文件由脚本从 `backend/app/**/*.py` 自动抽取（类/函数签名、导入、导出），
> 用于 Agent 快速建立「有哪些文件、有哪些可调用符号」的心智模型。
> 重新生成：仓库根保留生成脚本 `_gen_repomap.py`，直接运行 `python _gen_repomap.py` 即可刷新本文件。

---

## `app/__init__.py`

_(无顶层类/函数)_

---

## `app/database.py`

**imports**

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base
```

**symbols**

```
DATABASE_URL = ...
engine = ...
SessionLocal = ...
 def get_db()
```

---

## `app/dependencies.py`

> FastAPI 依赖（Dependency Injection）示例。

**imports**

```
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
```

**symbols**

```
class User(BaseModel):
FAKE_USER = ...
 def get_current_user(x_user_id)
 def require_admin(current_user)
```

---

## `app/main.py`

> 应用入口：只负责“装配” FastAPI 应用。

**imports**

```
from fastapi import FastAPI
from app.api.router import register_routes
from app.core.config import DESCRIPTION, TITLE, VERSION
from app.core.exception_handlers import device_not_found_handler, global_exception_handler
from app.core.exceptions import DeviceNotFoundError
from app.core.middleware import add_request_id, request_timing_middleware
```

**symbols**

```
app = ...
```

---

## `app/api/__init__.py`

> API 层：HTTP 接口与路由聚合。

_(无顶层类/函数)_

---

## `app/api/router.py`

> 路由聚合：把各业务 router 统一挂载到 app。

**imports**

```
from fastapi import FastAPI
from app.api.routes import demo_router, devices_router, health_router, users_router
from app.api.routes import protected
```

**symbols**

```
 def register_routes(app)
```

---

## `app/api/routes/__init__.py`

**imports**

```
from demo import router
from devices import router
from health import router
from users import router
```

**symbols**

```
__all__ = ...
```

---

## `app/api/routes/demo.py`

> 演示 / 实验路由：根路由、外部接口调用、日志测试。

**imports**

```
import httpx
from fastapi import APIRouter, HTTPException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from app.core.logging_config import logger, request_id_var
```

**symbols**

```
router = ...
@<decorator> def root()
@retry(...) async def call_external_api()
@<decorator> async def external_test()
@<decorator> def log_test()
@<decorator> def log_error_demo()
```

---

## `app/api/routes/devices.py`

**imports**

```
from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.services.device_service import get_device
from app.core.exceptions import DeviceNotFoundError
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.services import device_service
```

**symbols**

```
 def verify_device_token(x_device_token)
router = ...
@<decorator> def list_devices()
@<decorator> def get_device(device_id)
@<decorator> def create_device(data)
@<decorator> def update_device(device_id, data)
@<decorator> def delete_device(device_id)
```

---

## `app/api/routes/health.py`

**imports**

```
from fastapi import APIRouter
```

**symbols**

```
router = ...
@<decorator> def check_health()
```

---

## `app/api/routes/protected.py`

> 演示路由：把 Day9 的两个依赖用起来。

**imports**

```
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import User, get_current_user, require_admin
```

**symbols**

```
router = ...
DbSession = ...
CurrentUser = ...
@<decorator> def read_me(user)
@<decorator> def read_admin(user)
@<decorator> def ping_db(db)
```

---

## `app/api/routes/users.py`

**imports**

```
from fastapi import APIRouter, HTTPException, status
```

**symbols**

```
router = ...
FAKE_USERS = ...
@<decorator> def get_users()
@<decorator> def get_user(user_id)
```

---

## `app/core/__init__.py`

> 核心基础设施：配置、异常等。

_(无顶层类/函数)_

---

## `app/core/config.py`

> 应用配置：集中管理 FastAPI 实例的元数据。

**symbols**

```
TITLE = ...
DESCRIPTION = ...
VERSION = ...
```

---

## `app/core/exception_handlers.py`

> 全局 / 专用异常处理器。

**imports**

```
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DeviceNotFoundError
from app.core.logging_config import logger, request_id_var
```

**symbols**

```
 async def device_not_found_handler(request, exc)
 async def global_exception_handler(request, exc)
```

---

## `app/core/exceptions.py`

**symbols**

```
class DeviceNotFoundError(Exception):
```

---

## `app/core/logging_config.py`

> 日志与请求上下文（request_id）的集中配置。

**imports**

```
import logging
import sys
from contextvars import ContextVar
```

**symbols**

```
LOG_FORMAT = ...
class RequestIdFilter(logging.Filter):
   def filter(self, record)
logger = ...
```

---

## `app/core/middleware.py`

> HTTP 中间件：请求级横切逻辑集中在此。

**imports**

```
import time
import uuid
from fastapi import Request
from app.core.logging_config import logger, request_id_var
```

**symbols**

```
 async def add_request_id(request, call_next)
 async def request_timing_middleware(request, call_next)
```

---

## `app/models/__init__.py`

> SQLAlchemy ORM 模型包。

**imports**

```
from sqlalchemy.orm import declarative_base
from app.models.device import Device
```

**symbols**

```
Base = ...
__all__ = ...
```

---

## `app/models/device.py`

> 设备表 ORM 模型。

**imports**

```
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base
```

**symbols**

```
class Device(Base):
  __tablename__ = ...
```

---

## `app/schemas/__init__.py`

> 请求 / 返回的数据格式（Pydantic 模型）。

**imports**

```
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
```

**symbols**

```
__all__ = ...
```

---

## `app/schemas/device.py`

**imports**

```
from enum import Enum
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator
```

**symbols**

```
class DeviceType(str, Enum):
  router = ...
  switch = ...
  camera = ...
@field_validator(...) @classmethod def name_not_blank(cls, v)
class DeviceCreate(BaseModel):
class DeviceUpdate(BaseModel):
class DeviceResponse(BaseModel):
```

---

## `app/services/__init__.py`

> 业务逻辑层。

**imports**

```
from app.services.device_service import create_device, delete_device, get_device, list_devices, update_device
```

**symbols**

```
__all__ = ...
```

---

## `app/services/device_service.py`

**imports**

```
from app.schemas.device import DeviceCreate, DeviceUpdate
```

**symbols**

```
_next_id = ...
 def calculate_total(prices)
 def group_devices(devices)
 def filter_alarm_devices(devices, level)
 def list_devices()
 def get_device(device_id)
 def create_device(data)
 def update_device(device_id, data)
 def delete_device(device_id)
```

---

## `app/utils/__init__.py`

> 真正通用的小工具。

_(无顶层类/函数)_

---

