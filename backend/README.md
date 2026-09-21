# Atlas Device API

设备 API 已接 SQLAlchemy 持久化，默认使用固定的 backend/app.db，也可通过 DATABASE_URL 使用 PostgreSQL + psycopg 3。演示用户认证仍是假数据。

```powershell
cd E:\Codes\atlas-ai\backend
uv sync --locked
uv run pytest -q
uv run python -m exercises.day019_orm
uv run fastapi dev app/main.py
```

访问 `/health` 与 `/docs`。设备请求带 `x-device-token: secret-device-key`，这是本地教学值。启动时创建缺失表，不更改已有表结构；没有实现 Day 20 Alembic。

[Day 14～21 代码与 PostgreSQL 运行步骤](exercises/README.md) · [项目文档](../docs/index.md)
