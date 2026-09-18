# 模块：数据库与 ORM（database-models）

> 覆盖：`backend/app/database.py`、`backend/app/models/*.py`、`backend/app/schemas/device.py`

## 三层职责

| 层 | 文件 | 作用 |
|---|---|---|
| 引擎 / Session | `database.py` | 建引擎、`SessionLocal`、`get_db()`、`create_all` 建表 |
| ORM 模型 | `models/device.py`（`Base` 在 `models/__init__.py`） | 数据库表 `devices` 的映射 |
| 校验模型 | `schemas/device.py` | 请求体/响应体的 Pydantic 校验与序列化 |

> 经典对应：`DeviceCreate`（入参）→ `Device`（表）→ `DeviceResponse`（出参）。

## database.py

```python
DATABASE_URL = "sqlite:///./app.db"          # 相对“运行命令所在目录”
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)         # 学习阶段：启动即建表（生产用 Alembic）
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db() -> Session:                     # 见 dependency-injection.md
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## models/device.py（SQLAlchemy 2.0 风格）

```python
class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
```

`models/__init__.py` 定义 `Base = declarative_base()` 并导出 `Device`。

## schemas/device.py（Pydantic v2）

```python
class DeviceType(str, Enum):
    router = "router"
    switch = "switch"
    camera = "camera"

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1)
    device_type: DeviceType
    ip: IPvAnyAddress

class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    device_type: DeviceType | None = None
    ip: IPvAnyAddress | None = None

class DeviceResponse(BaseModel):
    id: int
    name: str
    device_type: DeviceType
    ip: str
```

- `name` 有 `@field_validator` 去空白、禁空。
- `device_type` 是枚举，非法值 → 422。
- `ip` 用 `IPvAnyAddress`，非法 IP → 422。

## 注意事项（重要）

- **`device_service` 当前没有使用 `Device` 表**：`GET/POST /devices` 读写的是内存 `_devices` 列表（`services/device_service.py`）。表已 `create_all` 建好，但 service 没接。改造时把 service 函数加 `db` 参数，用 `db.add` / `db.query(Device)` 等即可（参考 `services.md`）。
- **两个 `app.db`**：仓库根 `E:\Codes\atlas-ai\app.db` 与 `backend/app.db` 都存在。`DATABASE_URL` 相对运行目录，所以「你在哪个目录跑 `uv run`」决定用哪个库。排查数据不一致时先确认工作目录。
- 生产不要用 `create_all`，改用 Alembic 迁移。

## 相关文档

- 依赖注入（`get_db`）→ `dependency-injection.md`
- 业务层（如何接 DB）→ `services.md`
- 路由如何使用 schema → `routing.md`
