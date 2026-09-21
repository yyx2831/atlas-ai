# 项目总览（overview）

## 一句话定位

`atlas-ai` 是一个 **FastAPI 后端学习 / 演示工程**：用经典分层架构实现设备管理、用户、依赖注入演示、外部接口调用、日志与中间件等接口，便于边学边验证 FastAPI 的各种机制。

## 当前目标与阶段

- **阶段**：学习 + 演示。代码里保留了多个「Day N」标注的实验接口（`/external/test` 对应 httpx+tenacity，`/log-test`、`/log-error` 对应日志与中间件，`/me/*` 对应 Day9 依赖注入）。
- **已完成**：设备 CRUD 接入 Session 持久化，增加 User/Alarm ORM 和 SQL 练习；隔离 SQLite 测试通过，PostgreSQL 实机待验证。
- **不是**：生产级服务。鉴权是假用户、建表用 `create_all` 而非 Alembic、日志仅 stdout。

## 分层架构（顶层）

```
HTTP 请求
   ↓
middleware（request_id 注入 + 耗时统计）
   ↓
router / 路由层（api/routes）    ← 只管请求/响应与依赖装配
   ↓ 依赖注入（Depends）
services（业务逻辑）             ← 显式接收 Session
   ↓ 数据库 Session
models（SQLAlchemy ORM）  ↔  database（引擎/Session）
schemas（Pydantic 校验）   ← 请求体/响应体
core（配置/日志/中间件/异常/自定义异常）
```

## 工程边界

- 仓库根 `E:\Codes\atlas-ai\` 下有两类内容：
  - **代码**：`backend/`（uv 工程，真正可运行的 FastAPI 应用）。
  - **文档/配置**：`AGENTS.md`（入口）、`docs/`（本 Agent 上下文系统）、`ATLAS_AI_项目描述文档.md`（一次性全量单文件导出）、根 `.gitignore`、根 `app.db`。
- `backend/app/` 是可导入的 Python 包（flat layout）。`backend/AGENTS.md` 指向根目录文档。

## 关键产出（已验证）

- 启动：`uv run fastapi dev ./app/main.py`，`/docs` 显示全部 11 组接口。
- 中间件测试片段已修复（不再重建 `app` 实例），详见 `modules/entrypoint.md` 与 `modules/middleware-logging.md`。

## 相关文档

- 技术栈与版本 → `tech-stack.md`
- 完整目录与每文件职责 → `directory-map.md`
- 分层与请求流转 → `../architecture/overview.md`
