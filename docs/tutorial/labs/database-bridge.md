# Day 14～21：从现有内存 API 到 PostgreSQL

> 2026-09-21：已补实际代码，见 [运行入口](../../../backend/exercises/README.md)。本手册为原教学参考，不要再次整文件覆盖现有实现；当前额外含 User/Alarm 模型与 SQLite 便捷模式，Day 20 尚未实现。

本手册的代码是供你按课次实践的参考答案，不会自动修改项目。工作前查看 Git 差异；保持现有日志、路由认证与全局唯一 app。

## Day 14：先证明现在是什么状态

第一个 PowerShell：

```powershell
Set-Location E:\Codes\atlas-ai\backend
uv run fastapi dev app/main.py
```

第二个 PowerShell：

```powershell
$atlasHeaders = @{ 'x-device-token' = 'secret-device-key' }
$atlasBody = @{ name='lab-router'; device_type='router'; ip='192.0.2.10' } | ConvertTo-Json
$atlasDevice = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/devices -Headers $atlasHeaders -ContentType 'application/json' -Body $atlasBody
$atlasDevice
Invoke-RestMethod -Uri "http://127.0.0.1:8000/devices/$($atlasDevice.id)" -Headers $atlasHeaders
```

记下 ID，在第一个终端 Ctrl+C 后重新启动，在第二个终端查询。当前内存实现应找不到之前创建的设备；终端把 404 作为请求错误显示是正常现象。Day 21 后相同流程应仍返回设备。

观察状态码可用：

```powershell
curl.exe -i http://127.0.0.1:8000/devices
curl.exe -i -H "x-device-token: secret-device-key" http://127.0.0.1:8000/devices/999999
curl.exe -i -H "x-device-token: secret-device-key" http://127.0.0.1:8000/devices/not-an-int
```

预期分别为 401、404、422。当前固定 token 只是演示，不要沿用到生产。

## Day 15：单独建立 SQL 实验库

以下为 **WSL Ubuntu Bash**，不在 PowerShell 原样执行：

```bash
sudo apt update
sudo apt install postgresql postgresql-client
# systemd 已启用时：
sudo systemctl start postgresql
sudo -u postgres psql
```

在 psql 管理会话执行，仅在角色和库尚未存在的实验环境使用：

```sql
CREATE ROLE atlas_lab LOGIN;
\password atlas_lab
CREATE DATABASE atlas_lab OWNER atlas_lab;
CREATE DATABASE atlas_api_lab OWNER atlas_lab;
\q
```

`\password` 会提示输入本地练习密码，避免把密码贴进命令历史。`atlas_lab` 用于 SQL 实验，`atlas_api_lab` 留给 ORM 迁移。不要在真实业务库运行下面的种子脚本。

```bash
psql -h 127.0.0.1 -U atlas_lab -d atlas_lab -W
```

在 SQL 实验库执行一次：

```sql
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email text NOT NULL UNIQUE
);
CREATE TABLE devices (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL,
  device_type text NOT NULL CHECK (device_type IN ('router','switch','camera')),
  ip inet NOT NULL
);
CREATE TABLE alarms (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  device_id bigint NOT NULL REFERENCES devices(id),
  level text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO users(email) VALUES ('learner@example.test');
INSERT INTO devices(name,device_type,ip) VALUES
 ('router-A','router','192.0.2.10'),
 ('switch-B','switch','192.0.2.11'),
 ('camera-C','camera','192.0.2.12');
INSERT INTO alarms(device_id,level,created_at) VALUES
 (1,'critical',now()-interval '1 hour'),
 (1,'warning',now()-interval '2 hours'),
 (2,'warning',now()-interval '2 days');
SELECT id,name FROM devices ORDER BY id LIMIT 10;
BEGIN;
UPDATE devices SET name='temporary' WHERE id=1;
SELECT name FROM devices WHERE id=1;
ROLLBACK;
SELECT name FROM devices WHERE id=1;
```

最后一次查询应为 `router-A`。这份 SQL 实验的 `inet` 类型刻意与当前 ORM 字符串列不同，因此不要把它直接作为 API 的迁移起点。

## Day 16：最近 24 小时告警

```sql
SELECT d.id, d.name, COUNT(a.id) AS alarm_count
FROM devices AS d
LEFT JOIN alarms AS a
  ON a.device_id = d.id
 AND a.created_at >= now() - interval '24 hours'
GROUP BY d.id, d.name
ORDER BY alarm_count DESC, d.id ASC;
```

初始数据预期 `router-A=2`、`switch-B=0`、`camera-C=0`。时间条件在 ON 内，零告警设备仍保留。改成 WHERE 再比较；改成 COUNT(*) 再比较。一次只改一处，然后恢复。

## Day 17：执行计划实验

仅在独立实验库扩充数据：

```sql
INSERT INTO alarms(device_id,level,created_at)
SELECT (g % 3) + 1, 'warning', now() - g * interval '1 minute'
FROM generate_series(1,100000) AS g;
ANALYZE alarms;
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM alarms
WHERE device_id=1 AND created_at >= now()-interval '1 hour';
CREATE INDEX ix_alarms_device_time ON alarms(device_id,created_at);
ANALYZE alarms;
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM alarms
WHERE device_id=1 AND created_at >= now()-interval '1 hour';
```

记录 scan 类型、实际行数、过滤行数、buffers 与时间。重复查询会预热缓存；比较多个样本，不能把一次耗时差全归功于索引。`EXPLAIN ANALYZE` 会真的执行 SQL，所以不要随意对写语句使用。

## Day 18：事务失败实验

```sql
BEGIN;
INSERT INTO devices(name,device_type,ip)
VALUES ('must-rollback','router','192.0.2.99');
INSERT INTO alarms(device_id,level) VALUES (-999,'critical');
-- 上一条触发外键错误；事务内后续普通语句会失败。
ROLLBACK;
SELECT count(*) FROM devices WHERE name='must-rollback';
```

应为 0。身份序列出现编号空洞是正常现象，回滚不保证序号连续，不用填洞来“修复数据”。

## Day 19：不触碰现有数据库的 ORM 实验

在 `backend/exercises/day019.py` 保存以下代码，从 backend 执行 `uv run python -m exercises.day019`。创建 exercises 目录即可；也可加空 `__init__.py` 明确包结构。

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models import Base, Device

engine = create_engine('sqlite+pysqlite:///:memory:')
Base.metadata.create_all(engine)

with Session(engine) as db:
    row = Device(name='temporary', device_type='router', ip='192.0.2.1')
    db.add(row)
    db.flush()
    assert row.id is not None  # 已发 INSERT，但尚未提交
    db.rollback()
    assert list(db.scalars(select(Device))) == []

with Session(engine) as db:
    row = Device(name='saved', device_type='router', ip='192.0.2.2')
    db.add(row)
    db.commit()
    db.refresh(row)
    saved_id = row.id

with Session(engine) as db:
    assert db.get(Device, saved_id).name == 'saved'
```

这是只验证 ORM 生命周期的内存库，不证明跨进程持久化。注意只导入 models，不导入现有 database 模块，避免它在导入时 create_all 现有 app.db。

## Day 20：给空 API 实验库建立迁移

在 backend：

```bash
uv add 'psycopg[binary]' alembic
uv run alembic init migrations
```

在 `migrations/env.py` 顶部引入 `os`、`from app.models import Base, Device`，将 `target_metadata = None` 改为 `target_metadata = Base.metadata`。模型导入确保表进入 metadata，不需要导入会建表的 app.database。

读取 `DATABASE_URL` 并设置 Alembic 配置；URL 中的 `%` 需转义给 ConfigParser：

```python
database_url = os.environ['DATABASE_URL']
config.set_main_option('sqlalchemy.url', database_url.replace('%', '%%'))
```

在相同终端设置实际测试 URL，密码中的保留字符需 URL 编码。以下 `YOUR_URL_ENCODED_PASSWORD` 是必须替换的占位符，不是可直接使用的凭据：

```bash
# Ubuntu Bash
export DATABASE_URL='postgresql+psycopg://atlas_lab:YOUR_URL_ENCODED_PASSWORD@127.0.0.1:5432/atlas_api_lab'
uv run alembic revision --autogenerate -m 'create device table'
# 先打开 migrations/versions 新文件：应只创建当前 Device 表。
uv run alembic upgrade head
uv run alembic current
```

PowerShell 对应环境变量语法为 `$env:DATABASE_URL = 'postgresql+psycopg://...'`。环境变量只在当前终端及子进程生效。不要把含秘密的 URL 写到笔记或提交中。

第二个迁移练习：在 Device 模型加入 `description: Mapped[str | None] = mapped_column(String(255), nullable=True)`，生成迁移并审阅后 `upgrade head`。只在空或可丢弃测试库练 `downgrade -1` 再升级。真实数据上删除列不可逆地丢内容，不能当无风险操作。

## Day 21：替换 database.py 的连接管理

下面是 PostgreSQL 教学版本。完成 Day 20 后才应用，删除原来导入时运行的 `create_all`。使用这个版本时必须在启动终端设置 DATABASE_URL。

```python
import os
from collections.abc import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine(os.environ['DATABASE_URL'], pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db
```

这里没有 SQLite 的 `check_same_thread`。`pool_pre_ping` 能检测部分陈旧连接，不保证运行中的事务不会失败。

## Day 21：五个数据库 service

在 `services/device_service.py` 替换 CRUD 部分，保留已有 Python 学习辅助函数。这个阶段每个写服务代表一个完整业务事务；以后跨服务组合写入，应提升到共同事务边界，不能各自 commit。

```python
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Device
from app.schemas.device import DeviceCreate, DeviceUpdate

def list_devices(db: Session) -> list[Device]:
    return list(db.scalars(select(Device).order_by(Device.id)))

def get_device(device_id: int, db: Session) -> Device | None:
    return db.get(Device, device_id)

def create_device(data: DeviceCreate, db: Session) -> Device:
    device = Device(**data.model_dump(mode='json'))
    try:
        db.add(device)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(device)
    return device

def update_device(device_id: int, data: DeviceUpdate, db: Session) -> Device | None:
    device = db.get(Device, device_id)
    if device is None:
        return None
    # 延续现有局部更新语义：未传字段和显式 null 都忽略。
    updates = data.model_dump(mode='json', exclude_unset=True, exclude_none=True)
    try:
        for field, value in updates.items():
            setattr(device, field, value)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(device)
    return device

def delete_device(device_id: int, db: Session) -> bool:
    device = db.get(Device, device_id)
    if device is None:
        return False
    try:
        db.delete(device)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True
```

后续应给列表增加分页。此处保留原接口以便对比内存版与数据库版，不表示无限制列表适合生产。数据库错误在此回滚后继续抛出，由应用日志/异常层记录；不要把任意数据库故障伪装成 404。

## Day 21：路由与响应接线

给 `DeviceResponse` 增加 `model_config = ConfigDict(from_attributes=True)`，并从 pydantic 导入 ConfigDict，允许从 ORM 属性构造响应。

在当前设备路由中保留现有 router 的 prefix、tags、演示鉴权依赖及装饰器，只调整五个函数参数与 service 调用。导入：

```python
from typing import Annotated
from sqlalchemy.orm import Session
from app.database import get_db

Db = Annotated[Session, Depends(get_db)]
```

五个函数体参考（**保留原函数上方装饰器，不额外复制注册一组端点**）：

```python
def list_devices(db: Db):
    return device_service.list_devices(db)

def get_device(device_id: int, db: Db):
    device = device_service.get_device(device_id, db)
    if device is None:
        raise HTTPException(status_code=404, detail='设备不存在')
    return device

def create_device(data: DeviceCreate, db: Db):
    return device_service.create_device(data, db)

def update_device(device_id: int, data: DeviceUpdate, db: Db):
    device = device_service.update_device(device_id, data, db)
    if device is None:
        raise HTTPException(status_code=404, detail='设备不存在')
    return device

def delete_device(device_id: int, db: Db):
    if not device_service.delete_device(device_id, db):
        raise HTTPException(status_code=404, detail='设备不存在')
    return None
```

重新运行迁移并启动服务。再次执行本手册 Day 14 的创建和重启查询：现在设备应保留。再验证修改、删除、404、401、422，确认没有把鉴权与输入校验丢掉。

收尾同步 `docs/modules/services.md`、`database-models.md`、`routing.md` 的真实状态；如果签名改变，重新生成 repo-map。当前教程写入阶段不重跑该生成器，因为业务签名未变。
