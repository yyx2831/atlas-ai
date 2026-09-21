# 架构总览（architecture/overview）

## 设计原则

1. **单一职责 + 分层**：HTTP 只管收发（`api/routes`），校验交给 Pydantic（`schemas`），业务放进 `services`，持久化交给 `models` + `database`，横切逻辑（日志/中间件/异常）放进 `core`。
2. **入口只做装配**：`app/main.py` 不写业务，只负责「创建唯一 `FastAPI` 实例 → 挂路由 → 挂中间件 → 挂异常处理器」。任何业务逻辑都抽离到 `api/routes`、`core`、`services` 等模块。
3. **依赖注入贯穿全栈**：用户身份（`get_current_user`）、数据库 Session（`get_db`）都通过 `Depends` 注入端点，端点签名保持干净（`Annotated[Type, Depends(...)]`）。
4. **横切逻辑集中**：日志与 `request_id`、`RequestIdFilter` 在 `core/logging_config.py`；中间件在 `core/middleware.py`；异常处理器在 `core/exception_handlers.py`。避免重复定义与日志格式被覆盖。

## 分层关系图

```
                 ┌─────────────────────────────────────────┐
                 │            FastAPI app (main.py)         │
                 │  唯一实例：装配 路由/中间件/异常处理器      │
                 └─────────────────────────────────────────┘
                    │                  │                  │
        ┌───────────┴──────┐  ┌────────┴────────┐  ┌───────┴────────┐
        │  middleware 链    │  │  routers         │  │  exception      │
        │  add_request_id   │  │  (api/routes)    │  │  handlers       │
        │  request_timing   │  │                  │  │  (core/except.) │
        └───────────┬──────┘  └────────┬────────┘  └───────┬────────┘
                    │                  │                  │
                    └──────┬───────────┴───────────┬──────┘
                           │ 依赖注入 (Depends)      │
                    ┌──────┴───────┐        ┌────────┴────────┐
                    │ schemas       │        │ dependencies     │
                    │ (Pydantic)    │        │ get_current_user │
                    │ 请求/响应校验  │        │ get_db (Session) │
                    └──────┬───────┘        └────────┬────────┘
                           │                        │
                    ┌──────┴───────┐        ┌────────┴────────┐
                    │ services      │        │ database         │
                    │ (业务逻辑)    │        │ engine/Session   │
                    │ Session 持久化 │        └────────┬────────┘
                    └──────┬───────┘                 │
                           │                  ┌──────┴───────┐
                           │                  │ models (ORM)  │
                           │                  │ Device 表     │
                           └──────────────────┴──────────────┘
```

## 数据流向（读路径）

```
请求 → add_request_id（生成/透传 request_id，写入 request.state + contextvar）
     → request_timing_middleware（计时）
     → 路由端点（解析路径/查询/Body，经 Depends 注入 user / db）
     → service（业务处理，显式 Session）
     → model 经 Session 读写 SQLite / PostgreSQL
     → 响应 → request_timing_middleware（打印耗时日志）
            → add_request_id（把 request_id 写回响应头 X-Request-ID）
```

## 配置与元数据

- 应用元数据：`core/config.py` 的 `TITLE` / `DESCRIPTION` / `VERSION`，被 `main.py` 用于 `FastAPI(...)`。
- 数据库：`database.py` 的 读取 DATABASE_URL 环境变量（默认固定 backend/app.db），lifespan 中 init_db 创建缺失表。
- 日志：`logging_config.py` 配置 root logger（仅当无 handler 时），统一 `logger = logging.getLogger("app")`。

## 与「生产架构」的差异（当前是学习版）

| 维度 | 当前 | 生产建议 |
|---|---|---|
| 鉴权 | 假用户 `FAKE_USER` | 真实 JWT / OAuth，查库校验 |
| 建表 | `create_all` 启动时 | Alembic 迁移 |
| 业务数据 | Device 表 + get_db | 补分页、迁移与真实认证 |
| 日志 | stdout | 文件 / 集中日志（ELK 等） |
| 全局异常 | 捕获裸 `Exception` | 只捕获自定义业务异常基类 |
| 路由前缀 | 无 `/api` | 通常加 `/api/v1` 版本前缀 |

## 相关文档

- 一次请求的完整流转 → `request-lifecycle.md`
- 每个模块的细节 → `../modules/*.md`
- 文件位置 → `../project/directory-map.md`
