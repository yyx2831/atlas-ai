# 目录结构图（directory-map）

> 排除生成物：`.venv/`、`__pycache__/`、`uv.lock`（锁文件）、`app.db`（运行时）、`.git/`。
> 完整源码转录见根目录 `ATLAS_AI_项目描述文档.md`；签名级索引见 `../generated/repo-map.md`。

```
atlas-ai/                              ← 仓库根
├── AGENTS.md                          # Agent 入口地图（本项目约定）
├── ATLAS_AI_项目描述文档.md            # 一次性全量单文件导出（给外部 ChatGPT 用）
├── .gitignore                         # 根级忽略（Python/虚拟环境/IDE/OS）
├── app.db                             # 根目录 SQLite（运行时生成，可忽略）
├── docs/                              # ← 本 Agent 上下文系统（可维护的权威源）
│   ├── index.md                       #   文档地图（导航）
│   ├── project/{overview,tech-stack,directory-map}.md
│   ├── architecture/{overview,request-lifecycle}.md
│   ├── modules/{entrypoint,routing,dependency-injection,database-models,services,middleware-logging,error-handling}.md
│   └── generated/repo-map.md          #   脚本抽取的源码签名地图
│
└── backend/                           # ← 代码根（uv 工程，真正可运行）
    ├── AGENTS.md                      #   子目录指针，指向根 AGENTS.md / docs/
    ├── .gitignore                     #   后端专用忽略（含 .venv/、app.db、*.log、.env）
    ├── .python-version                #   uv 锁定版本：3.12
    ├── README.md                      #   空占位（待补充）
    ├── pyproject.toml                 #   ★ 工程配置：依赖 + uv_build 包指向 app/
    ├── uv.lock                        #   uv 解析的锁定文件（自动生成）
    ├── app.db                         #   后端目录内 SQLite（运行时生成，可忽略）
    │
    ├── app/                           # ★ 可导入包（flat layout）
    │   ├── __init__.py                #   包标识（空）
    │   ├── main.py                    # ★ 入口：唯一 FastAPI 实例 + 装配（不再写业务）
    │   ├── database.py                # ★ 引擎 + SessionLocal + get_db() 依赖
    │   ├── dependencies.py            # ★ DI：User / FAKE_USER / get_current_user / require_admin
    │   │
    │   ├── api/
    │   │   ├── __init__.py            #   包标识（docstring）
    │   │   ├── router.py              # ★ register_routes(app)：集中挂载所有子路由
    │   │   └── routes/
    │   │       ├── __init__.py        #   聚合导出 4 个 router（含 demo_router）
    │   │       ├── demo.py            #   根路由 / + /external/test + /log-test + /log-error
    │   │       ├── devices.py         #   设备管理 CRUD（前缀 /devices，token 守卫）
    │   │       ├── health.py          #   系统运维 /health
    │   │       ├── users.py           #   用户管理 /users（假数据）
    │   │       └── protected.py       #   当前用户 DI 演示 /me、/me/admin、/me/ping-db
    │   │
    │   ├── core/
    │   │   ├── __init__.py            #   包标识（docstring）
    │   │   ├── config.py              #   TITLE/DESCRIPTION/VERSION（应用元数据）
    │   │   ├── exceptions.py          #   自定义异常 DeviceNotFoundError
    │   │   ├── logging_config.py      #   ★ logger + RequestIdFilter + request_id_var
    │   │   ├── middleware.py          #   ★ add_request_id + request_timing_middleware
    │   │   └── exception_handlers.py  #   ★ device_not_found_handler + global_exception_handler
    │   │
    │   ├── models/
    │   │   ├── __init__.py            #   Base = declarative_base()，导出 Device
    │   │   └── device.py              #   ORM 模型 Device（devices 表）
    │   │
    │   ├── schemas/
    │   │   ├── __init__.py            #   导出 DeviceCreate/Update/Response
    │   │   └── device.py              #   Pydantic + DeviceType 枚举 + 校验器
    │   │
    │   ├── services/
    │   │   ├── __init__.py            #   导出 device_service 的 5 个函数
    │   │   └── device_service.py      #   业务逻辑（SQLAlchemy 持久化）
    │   │
    │   └── utils/
    │       └── __init__.py            #   包标识（docstring，占位）
    │
    └── docs/
        └── Day9-Dependency-Injection.md  # Day9 依赖注入学习笔记（配套讲解本工程代码）
```

## 各文件职责速查

| 文件 | 职责 |
|---|---|
| `backend/pyproject.toml` | 依赖声明 + `uv_build` 包指向 `app/` |
| `backend/app/main.py` | **唯一**创建 `FastAPI` 实例；装配路由、中间件、异常处理器 |
| `backend/app/api/router.py` | `register_routes(app)` 集中 `include_router` 全部子路由（devices 只注册一次） |
| `backend/app/core/config.py` | 应用元数据 `TITLE` / `DESCRIPTION` / `VERSION` |
| `backend/app/core/logging_config.py` | 全局 `logger`、`RequestIdFilter`、`request_id_var`（防重复添加 handler） |
| `backend/app/core/middleware.py` | `add_request_id`（request_id 注入）、`request_timing_middleware`（耗时统计） |
| `backend/app/core/exception_handlers.py` | `device_not_found_handler`、`global_exception_handler`（兜住未捕获异常） |
| `backend/app/core/exceptions.py` | 自定义异常 `DeviceNotFoundError` |
| `backend/app/database.py` | SQLite/PostgreSQL 引擎、显式 init_db、SessionLocal、get_db |
| `backend/app/dependencies.py` | `User`、`FAKE_USER`、`get_current_user`、`require_admin` |
| `backend/app/models/device.py` | ORM 模型 `Device` |
| `backend/app/schemas/device.py` | `DeviceType` 枚举 + `DeviceCreate/Update/Response` |
| `backend/app/services/device_service.py` | 设备业务函数（显式 Session） |
| `backend/app/api/routes/*.py` | 各业务路由（见 `../modules/routing.md`） |
| `backend/docs/Day9-Dependency-Injection.md` | 依赖注入学习笔记 |

## 找文件的小技巧

- 找某函数/类定义 → `../generated/repo-map.md`（按文件列出 `def` / `class`）。
- 找某路由路径 → `../modules/routing.md`（按 tag 分组列出全部端点）。
- 找「为什么这么设计」→ `../architecture/overview.md` 与 `../modules/*.md` 的「注意事项」。

## 学习教程目录（新增）

`docs/tutorial/` 是面向学习者的教程，不替代上方反映当前源码的模块文档。

```text
docs/tutorial/
├── README.md                 # 180 课导航
├── START-HERE.md             # 已有代码衔接与建议起点
├── PROGRESS.md               # 学习者自行验收的进度
├── ENVIRONMENT.md            # Windows / WSL / 路径与数据约定
├── SOURCES.md                # 官方资料与核查范围
├── original-plan.md          # 用户原始计划备份
├── days/day-001.md … day-180.md
├── labs/database-bridge.md   # Day 14～21 参考实验
├── labs/key-recipes.md       # 关键代码与配置示例
└── templates/daily-note.md   # 每日学习记录模板
```

本次仅新增教程与导航，没有增删业务源码或改变签名，因此保留 `docs/generated/repo-map.md` 的源码地图内容。

## 2026-09-21 新增代码

- backend/app/models/user.py、alarm.py：用户、告警 ORM。
- backend/exercises/day019_orm.py：临时库 ORM/JOIN/回滚实验。
- backend/exercises/sql/day015_basics.sql、day016_join.sql、day017_indexes.sql、day018_transactions.sql。
- backend/exercises/compose.postgres.yaml：仅绑定本机 55432 的 PostgreSQL 实验服务。
- backend/exercises/README.md：完整运行入口。
- backend/tests/test_schemas.py、test_device_api.py：校验、CRUD、回滚、跨进程持久化。
