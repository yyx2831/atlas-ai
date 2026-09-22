# Atlas 后端

完整启动见 [项目 README](../README.md)。

```powershell
uv sync --locked
uv run python -m app.cli init --email you@example.com --demo
uv run fastapi dev app/main.py
```

先停服务再运行带 --demo 的初始化，避免本地 Qdrant 目录锁冲突。已有账号不覆盖密码。默认 backend/app.db，根目录旧数据库保留；服务没有内置默认账户。登录用新 Account 表，原 User 只作数据库教学。

POST /auth/login 返回 JWT，后续请求带 Authorization: Bearer。旧固定 token 已停用。管理员写设备/告警，普通成员只读；每个账户独立持有文档、聊天和分析记录。完整路由见 /docs；/users 和旧外部调用演示未挂载。

配置集中 app/core/settings.py，环境变量覆盖本目录 .env。默认 demo 模式不调用付费模型；真实 API 见 [模型配置](../docs/LOCAL-MODELS.md)。参数及维护见 [代码维护](../docs/MAINTENANCE.md)。

运行 uv run pytest -q；测试使用临时数据与模拟模型。部署用单 worker。SQL create_all 不做列迁移，新增/修改已有列需显式迁移。文档同步索引不适合高并发；现有上限和状态恢复见 [RAG 文档](../docs/modules/rag.md)。
