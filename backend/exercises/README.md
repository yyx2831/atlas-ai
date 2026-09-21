# Day 14、15、16、17、18、19、21 代码入口

你已看过这些课程；这里把代码补齐，但“已看完 / 已提供代码 / 自己能独立完成”仍分开记录。Day 20 Alembic 暂未实现，教学阶段通过 create_all 创建缺失表。

## 先跑不依赖 Docker 的部分

PowerShell，工作目录固定为 backend：

```powershell
Set-Location E:\Codes\atlas-ai\backend
uv sync --locked
uv run pytest -q
uv run python -m exercises.day019_orm
uv run fastapi dev app/main.py
```

- Day 14：`tests/test_device_api.py` 覆盖路由、响应、演示认证、422/404、request_id 与 CRUD。
- Day 19：`day019_orm.py` 在临时文件库创建 User、Device、Alarm；演示 flush/commit、LEFT JOIN、唯一约束失败及 rollback。结束自动清理临时库，不使用你的 app.db。
- Day 21：`app/services/device_service.py` 是数据库版 CRUD；路由显式注入 Session。`test_restarted_process_reads_same_database` 使用两个独立进程证明数据持久化。

访问 `/docs`，设备接口仍需头 `x-device-token: secret-device-key`（仅本地演示）。默认数据库固定为 `backend/app.db`，不会因工作目录变动而换库。仓库根旧的 app.db 原样保留，未自动合并。

创建一条设备、重启开发服务、再次查询，应仍存在。原有 PUT 保留局部更新语义：未传字段和 null 忽略，删除不存在 ID 返回 404。

## Day 15～18：真正的 PostgreSQL SQL 实验

当前机器的 Docker daemon 未运行，所以此次只准备了这些脚本，尚未完成 PostgreSQL 实机验证。先自行启动 Docker Desktop 的 Linux 容器服务，确认 `docker info` 成功。

```powershell
Set-Location E:\Codes\atlas-ai\backend
# 设置自选实验密码；这个字符串是占位符，不应原样用于部署。
$env:ATLAS_LAB_PASSWORD = '替换为自选实验密码'
docker compose -f exercises/compose.postgres.yaml up -d --wait
docker compose -f exercises/compose.postgres.yaml exec -T postgres psql -U atlas_lab -d atlas_lab -f /lessons/day015_basics.sql
docker compose -f exercises/compose.postgres.yaml exec -T postgres psql -U atlas_lab -d atlas_lab -f /lessons/day016_join.sql
docker compose -f exercises/compose.postgres.yaml exec -T postgres psql -U atlas_lab -d atlas_lab -f /lessons/day017_indexes.sql
docker compose -f exercises/compose.postgres.yaml exec -T postgres psql -U atlas_lab -d atlas_lab -f /lessons/day018_transactions.sql
```

顺序与预期：

1. Day 15 在独立 `atlas_course` schema 建表和插入三台设备。UPDATE/DELETE 用 SAVEPOINT 回滚，可重复执行，不操作业务 public 表。
2. Day 16 事务内临时插入告警，LEFT JOIN 预期 2、0、0；错误的 WHERE 对照只保留有告警设备，结束回滚告警。
3. Day 17 在临时表生成十万行，对比复合索引前后 EXPLAIN ANALYZE；事务结束丢弃临时表。比较实际扫描与 buffers，不保证固定加速倍数。
4. Day 18 演示显式 ROLLBACK，以及失败子事务的整体回滚；`should_be_zero` 应为 0，并输出外键失败已回滚的 NOTICE。

容器端口只绑定本机 `55432`，避免占用已有 PostgreSQL 的默认 5432。实验数据在专用命名卷；停止用 `docker compose -f exercises/compose.postgres.yaml stop`，不要加 `down -v` 删除卷。首次初始化后改密码环境变量不会自动修改卷内已有账户密码。

## Day 21：API 切换到 PostgreSQL

完成上面的启动后，在同一个 PowerShell 终端：

```powershell
$atlasEncodedPassword = [uri]::EscapeDataString($env:ATLAS_LAB_PASSWORD)
$env:DATABASE_URL = "postgresql+psycopg://atlas_lab:${atlasEncodedPassword}@127.0.0.1:55432/atlas_lab"
uv run python -m app.database
uv run fastapi dev app/main.py
```

API 使用默认 public schema，SQL 课程使用 atlas_course，不会把 SQL 练习的 inet 字段与 ORM 的字符串字段混在同一张表。切换 PostgreSQL 不会自动搬迁 SQLite 数据，所以看到不同设备列表是预期现象。当前认证用户仍是假用户，与新 ORM User 表分开。

恢复 SQLite：停止服务，再执行 `Remove-Item Env:DATABASE_URL` 后重新启动。环境变量由应用读取，不自动加载任意 .env 文件。

## 阅读代码的顺序

1. `app/models/device.py`、`alarm.py`、`user.py`：表、关系、外键、唯一约束和复合索引。
2. `app/database.py`：环境配置、SQLite 外键开关、Session 生命周期与 init_db。
3. `app/services/device_service.py`：select、get、commit、rollback 与 JSON 转换。
4. `app/api/routes/devices.py`：Depends 只在路由解析，再显式传 db。
5. `tests/test_device_api.py`：状态码、级联删除、回滚后继续使用 Session、跨进程持久化。

一个写 service 就是一个事务；以后组合多个写 service 时要提升公共事务边界，不能每一步各自提交。create_all 只补缺失表，不会修改已有字段；Day 20 仍需补迁移知识。当前列表未分页、认证仍是演示，不作为生产版本。
