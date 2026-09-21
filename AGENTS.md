# AGENTS.md — Agent 项目上下文入口

> 本文件是给 AI Agent 的「项目地图」，不是给人看的 README。
> 目标：让 Agent 在几秒内建立项目心智模型，再按需加载细节，**不要扫描整个仓库**。

## 这是什么项目

`atlas-ai` 是一个 **FastAPI 后端学习 / 演示工程**，用典型分层架构（`api/routes` → `schemas` → `services` → `models` → `database`）实现设备管理、用户、当前用户 DI 演示、外部接口调用、日志与中间件等接口。设备 CRUD 已持久化；用户认证仍为演示，支持 SQLite 和 PostgreSQL。

- **代码根目录**：`backend/`（uv 工程，`pyproject.toml` 在此）
- **可导入包**：`backend/app/`（flat layout，`pyproject.toml` 用 `[tool.uv.build-backend]` 指明 `module-name = "app"`）
- **完整单文件导出**：`ATLAS_AI_项目描述文档.md`（一次性全量转录，仅供整体粘贴给外部 ChatGPT；本 `docs/` 才是可维护的权威源）

## 技术栈

- Python ≥ 3.12，包管理 **uv**（`uv run`、`uv add`）
- Web 框架 **FastAPI**（`fastapi[standard]`）
- ORM **SQLAlchemy 2.0**（`Mapped` / `mapped_column`），SQLite 本地库
- 数据校验 **Pydantic v2**
- 外部调用 **httpx** + 重试 **tenacity**
- 服务器 uvicorn（FastAPI 内置）

## 如何开始一个任务（必读顺序）

1. **先读** `docs/index.md` —— 它就是目录地图。
2. 根据任务类型，从 `docs/index.md` 选对应模块文档读：
   - 改接口 / 加路由 → `docs/modules/routing.md`
   - 改依赖注入（用户、数据库 Session）→ `docs/modules/dependency-injection.md`
   - 改数据库 / ORM 模型 → `docs/modules/database-models.md`
   - 改业务函数 → `docs/modules/services.md`
   - 改入口装配 / 启动 → `docs/modules/entrypoint.md`
   - 改中间件 / 日志 → `docs/modules/middleware-logging.md`
   - 改异常处理 → `docs/modules/error-handling.md`
3. 需要快速看「有哪些文件、有哪些类/函数」→ `docs/generated/repo-map.md`（由脚本从源码抽取，可随时重新生成）。
4. **只有确认要改的模块，再打开对应 `backend/app/...` 源码**。

## 关键约定（违反会踩坑）

- **路由没有 `/api` 前缀**：`/health`、`/devices`、`/users`、`/me`、`/external/test`、`/log-test`、`/log-error` 都是根级路径。
- **`app` 实例全局唯一**：`backend/app/main.py` 是**唯一**创建 `FastAPI` 实例的地方。任何「中间件测试 / 实验」代码都只能 `app.middleware("http")(func)` 注册到这个实例，**绝不能写 `app = FastAPI(...)` 再建一个实例**——否则前面的路由会被覆盖，`/docs` 只剩零星接口（历史真实 bug，已修复）。
- **依赖注入两件套**：`get_db()`（每请求一个 SQLAlchemy Session）和 `get_current_user()`（当前是假用户）都放在 `app/dependencies.py` + `app/database.py`，端点用 `Annotated[Type, Depends(...)]` 注入。
- **日志带 request_id**：统一用 `from app.core.logging_config import logger`，格式 `时间 | 级别 | request_id | 模块 | 消息`，禁止 `print()`。

## 常用命令

```bash
cd backend
uv run fastapi dev ./app/main.py     # 本地开发服务器（端口 8000）
uv run python -c "..."               # 跑一段脚本
uv add <pkg>                          # 加依赖（会写 pyproject.toml 并装进 .venv）
```

## 已知坑 / 待办

1. 设备 service 已显式接收 Session；Depends 仅在路由解析。每个写 service 自行 commit/rollback，组合事务需重新设计边界。
2. 默认 SQLite 路径固定为 backend/app.db；根目录旧 app.db 保留但默认不读取。DATABASE_URL 可切换 PostgreSQL。
3. **`uv_build` 包指向**：`pyproject.toml` 的 `[tool.uv.build-backend]` 已配置 `module-name="app"`，删/改包目录后必须同步此配置，否则 `uv run fastapi dev` 报 `Expected a Python module at: src/backend/__init__.py`。
4. backend/README.md 与 exercises/README.md 提供运行入口。Day 20 Alembic 尚未实现，lifespan 用 init_db 仅建缺失表。
5. **同步端点（如 `log_test`）经线程池执行**，中间件 `request_timing_middleware` 里 request_id 偶尔为空（contextvar 传递问题），属已知 quirk、无害。

## 改完代码后必须同步更新文档

代码变更后，按「影响范围」更新本 `docs/` 对应文件（目录树、模块文档、repo-map）：

- 文件增删 / 路由增删 → 更新 `docs/project/directory-map.md`、`docs/generated/repo-map.md`、`docs/index.md`
- 某模块行为变化 → 更新对应 `docs/modules/*.md`
- 不确定影响 → 至少更新 `docs/generated/repo-map.md`（重跑生成脚本）

> 不要写 10000 行的 AGENTS.md。保持本文件为「地图」，知识放在 `docs/` 里。
