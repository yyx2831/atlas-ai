# atlas-ai 后端项目 · 完整描述文档

> ⚠️ **本文件是「一次性全量单文件导出」**，用于直接整段复制粘贴到网页版 ChatGPT 发送。
> **可维护的权威文档源是 `docs/`（Agent 上下文系统）**：`AGENTS.md`（入口地图）+ `docs/index.md`（导航）+ `docs/project|architecture|modules|generated/` 分层文档。
> 代码变更后，请先更新 `docs/`（及 `docs/generated/repo-map.md`），本文件可按需由 `docs/` + 源码重新生成，不必逐行手维护。

> 用途：本文件是 `E:\Codes\atlas-ai\` 项目的**单文件、自包含描述**，可直接整段复制粘贴到网页版 ChatGPT 对话框发送。
> 包含：① 完整目录结构树 ② 各文件/模块功能说明 ③ 主要源码文件的完整内容与关键注释。
> 项目性质：一个**学习用途**的 FastAPI 后端，逐步演示依赖注入、SQLAlchemy、日志、异常处理器、外部 HTTP 调用（httpx + tenacity）等知识点。代码全部可运行。

---

## 一、项目概览

- **项目名**：`atlas-ai`（Python 包名 `backend`，可导入源码目录为 `backend/app/`）。
- **技术栈**：
  - Python `>=3.12`（开发机 `.python-version` 锁定 `3.12`）
  - FastAPI `>=0.141.1`（含 `standard` 扩展，自带 uvicorn）
  - SQLAlchemy `>=2.0.54`（ORM + 建表）
  - httpx `>=0.28.1`（异步 HTTP 客户端，用于调用外部接口）
  - tenacity `>=9.1.4`（重试装饰器，用于接口抖动重试）
- **包管理**：`uv`（`uv_build` 作为构建后端，`pyproject.toml` + `uv.lock`）。
- **架构分层**（FastAPI 经典分层，已做模块化抽离）：
  - `api/routes/`：HTTP 路由层（只管请求/响应与依赖装配）
  - `api/router.py`：路由聚合层（`register_routes(app)` 集中 `include_router` 所有子路由，避免 `main.py` 散落挂载）
  - `schemas/`：Pydantic 数据模型层（请求体/响应体校验与序列化）
  - `services/`：业务逻辑层（目前是内存版假数据，尚未接数据库）
  - `models/`：SQLAlchemy ORM 模型层（数据库表映射）
  - `core/`：核心基础设施，已细分为——
    - `core/config.py`：FastAPI 实例元数据（`TITLE`/`DESCRIPTION`/`VERSION`）
    - `core/logging_config.py`：root logger 配置、`RequestIdFilter`、`request_id_var`、统一 `logger`
    - `core/middleware.py`：HTTP 中间件（`add_request_id` 注入 request_id、`request_timing_middleware` 中间件测试）
    - `core/exception_handlers.py`：异常处理器（`device_not_found_handler`、`global_exception_handler` 兜底）
    - `core/exceptions.py`：自定义异常类（`DeviceNotFoundError`）
  - `dependencies.py`：依赖注入函数（`get_current_user`、`require_admin`）
  - `database.py`：数据库引擎、Session 工厂、`get_db` 依赖
  - `main.py`：应用**装配**入口——只创建**唯一** `FastAPI` 实例，然后调用 `register_routes` 挂载路由、注册中间件、注册异常处理器；**不再内联任何业务/配置逻辑**（历史上曾把所有内容写进 `main.py`，已抽离）
- **数据库**：SQLite，文件 `app.db`（由 `Base.metadata.create_all` 在启动时自动创建，学习阶段使用，生产应改 Alembic 迁移）。
- **重要约定**：所有路由**没有 `/api` 前缀**，直接是 `/health`、`/devices`、`/me`、`/users`（这是容易被忽略的实测要点）。

---

## 二、完整目录结构树

> 说明：以下树已**排除** `.git/`（版本库）、`.venv/`（虚拟环境）、`__pycache__/`（字节码缓存）、`.workbuddy/`（WorkBuddy 项目记忆，非源码）。`app.db` 是运行时生成的 SQLite 文件。

```
atlas-ai/
├── .gitignore                         # 根级忽略规则（Python/虚拟环境/IDE/OS）
├── app.db                             # 根目录 SQLite（运行时生成，可忽略）
├── ATLAS_AI_项目描述文档.md            # 本文件（项目单文件描述，需与代码同步更新）
│
└── backend/                           # 后端项目根（uv 工程）
    ├── .gitignore                     # 后端专用忽略规则（含 .venv/、app.db、*.log、.env）
    ├── .python-version                # uv 锁定的 Python 版本：3.12
    ├── README.md                      # 占位文件（当前为空，待补充）
    ├── pyproject.toml                 # ★ 工程配置（依赖声明 + uv_build 包指向 app/）
    ├── uv.lock                        # uv 解析出的依赖锁定文件（自动生成）
    ├── app.db                         # 后端目录内 SQLite（运行时生成，可忽略）
    │
    ├── app/                           # ★ 可导入的 Python 包（flat layout）
    │   ├── __init__.py                # 包标识（空）
    │   ├── main.py                    # ★ 装配入口：创建唯一 app 实例 + 调 register_routes + 注册中间件/异常处理器
    │   ├── database.py                # ★ 数据库引擎 + SessionLocal + get_db() 依赖
    │   ├── dependencies.py            # ★ DI 函数：User/FAKE_USER/get_current_user/require_admin
    │   │
    │   ├── api/
    │   │   ├── __init__.py            # 包标识（docstring）
    │   │   ├── router.py              # ★ 路由聚合：register_routes(app) 统一 include 所有子 router
    │   │   └── routes/
    │   │       ├── __init__.py        # 聚合导出 health_router/users_router/devices_router/demo_router
    │   │       ├── health.py          # 健康检查路由 /health
    │   │       ├── devices.py         # 设备 CRUD 路由 /devices（带 token 守卫）
    │   │       ├── users.py           # 用户列表路由 /users（假数据）
    │   │       ├── protected.py       # 演示路由 /me、/me/admin、/me/ping-db（DI 教学）
    │   │       └── demo.py            # 演示/实验路由：/、/external/test、/log-test、/log-error
    │   │
    │   ├── core/
    │   │   ├── __init__.py            # 包标识（docstring）
    │   │   ├── exceptions.py          # 自定义异常 DeviceNotFoundError
    │   │   ├── config.py              # ★ FastAPI 元数据 TITLE/DESCRIPTION/VERSION
    │   │   ├── logging_config.py      # ★ 日志配置：root logger、RequestIdFilter、request_id_var、统一 logger
    │   │   ├── middleware.py          # ★ HTTP 中间件：add_request_id、request_timing_middleware（中间件测试）
    │   │   └── exception_handlers.py  # ★ 异常处理器：device_not_found_handler、global_exception_handler
    │   │
    │   ├── models/
    │   │   ├── __init__.py            # 定义 Base = declarative_base()，并导出 Device
    │   │   └── device.py             # ORM 模型 Device（对应 devices 表）
    │   │
    │   ├── schemas/
    │   │   ├── __init__.py            # 导出 DeviceCreate/DeviceUpdate/DeviceResponse
    │   │   └── device.py             # Pydantic 模型 + DeviceType 枚举 + 校验器
    │   │
    │   ├── services/
    │   │   ├── __init__.py            # 导出 device_service 的 5 个函数
    │   │   └── device_service.py      # 业务逻辑（内存版假数据，未接 DB）
    │   │
    │   └── utils/
    │       └── __init__.py            # 包标识（docstring，占位）
    │
    └── docs/
        └── Day9-Dependency-Injection.md  # Day9 依赖注入学习笔记（配套讲解本工程代码）
```

---

## 三、各文件与模块功能说明

### 根目录
| 文件 | 功能 |
|---|---|
| `atlas-ai/.gitignore` | 根级忽略规则：Python 编译产物、`__pycache__`、`*.egg-info`、虚拟环境、`.workbuddy/` 项目记忆、IDE（`.idea`/`.vscode`）、OS 文件（`.DS_Store`）。 |
| `atlas-ai/app.db` | 根目录 SQLite 数据库文件（由 `create_all` 生成；与 `backend/app.db` 可能同时存在，需注意当前代码 `DATABASE_URL="sqlite:///./app.db"` 指向**运行目录**下，即 `backend/app.db`）。 |

### `backend/` 工程根
| 文件 | 功能 |
|---|---|
| `backend/.gitignore` | 后端专用忽略：Python 生成物、`.venv/`、`.env`/`*.env`、日志 `*.log`、本地数据库 `app.db`/`*.sqlite`/`*.sqlite3`。 |
| `backend/.python-version` | `uv` 用的 Python 版本锁文件，内容 `3.12`。 |
| `backend/README.md` | 占位文件，当前为空（仅 1 个空行），待后续补充工程说明。 |
| `backend/pyproject.toml` | **工程核心配置**：声明项目元信息、依赖、`build-system`（uv_build），并用 `[tool.uv.build-backend]` 告知构建后端真实包在 `app/` 而非 `src/backend/`。详见第四节。 |
| `backend/uv.lock` | `uv` 解析并锁定的完整依赖树（自动生成，不应手改）。记录了 `fastapi`、`sqlalchemy`、`httpx`、`tenacity` 及其传递依赖（如 `starlette`、`pydantic`、`uvicorn`、`httpcore`、`h11`、`anyio`、`tenacity` 等）的精确版本与哈希。 |
| `backend/app.db` | 运行时由 `Base.metadata.create_all(bind=engine)` 自动生成的 SQLite 文件（当前 `DATABASE_URL` 指向运行目录的 `./app.db`，即从 `backend/` 启动时是 `backend/app.db`）。 |

### `backend/app/` 源码包
| 文件 | 功能 |
|---|---|
| `app/__init__.py` | 让 `app` 成为 Python 包（空文件）。 |
| `app/main.py` | **装配入口（极薄）**。只做四件事：① 创建**唯一** `FastAPI` 应用（元数据来自 `core/config`）；② 调用 `register_routes(app)` 挂载所有子路由；③ 注册两个中间件（`add_request_id`、`request_timing_middleware`）；④ 注册两个异常处理器（`device_not_found_handler`、`global_exception_handler`）。**不内联任何业务/配置/日志/中间件代码**——这些已抽离到 `core/` 与 `api/router.py`。详见第四节。 |
| `app/database.py` | 数据库连接核心：`DATABASE_URL`、SQLite 引擎、`Base.metadata.create_all` 自动建表、`SessionLocal` 工厂、`get_db()` yield 依赖（每请求一个 Session，结束自动 `close`）。详见第四节。 |
| `app/dependencies.py` | FastAPI 依赖注入示例：`User` Pydantic 模型、`FAKE_USER` 假用户、`get_current_user()`（读取 `X-User-Id` 头，默认返回假用户）、`require_admin()`（嵌套依赖，校验管理员）。详见第四节。 |

### `backend/app/api/`
| 文件 | 功能 |
|---|---|
| `router.py` | **路由聚合**：`register_routes(app)` 函数集中 `include_router` 所有子路由（`health_router`、`users_router`、`devices_router`、`protected.router`、`demo_router`），避免原 `main.py` 中 `devices` 重复 include 的问题。 |
| `routes/__init__.py` | 聚合导出 `health_router`、`users_router`、`devices_router`、`demo_router`，供 `api/router.py` 统一挂载。 |
| `routes/health.py` | `GET /health` → 返回 `{"status":"healthy","database":"connected"}`。 |
| `routes/devices.py` | 设备 CRUD：`/devices` 列表、`/devices/{id}` 查询/更新/删除、`POST /devices` 创建。整条路由通过 `dependencies=[Depends(verify_device_token)]` 挂载 token 校验（请求头 `X-Device-Token` 必须等于 `secret-device-key`）。调用 `device_service` 的对应函数。 |
| `routes/users.py` | `GET /users` 列表、`GET /users/{id}` 查询，数据来自模块内 `FAKE_USERS` 假列表。 |
| `routes/protected.py` | Day9 DI 教学路由：`GET /me`（注入当前用户）、`GET /me/admin`（要求管理员，嵌套依赖）、`GET /me/ping-db`（注入 DB Session 验证可用）。 |
| `routes/demo.py` | 演示/实验路由（从原 `main.py` 内联抽出）：`GET /`（根路由）、`GET /external/test`（httpx + tenacity 重试外部接口）、`GET /log-test`（日志测试）、`GET /log-error`（异常 + 全局处理器演示）。 |

### `backend/app/core/`
| 文件 | 功能 |
|---|---|
| `exceptions.py` | 自定义异常 `DeviceNotFoundError`，供 `exception_handlers.py` 的专用异常处理器捕获返回 404。 |
| `config.py` | 集中管理 FastAPI 实例元数据：`TITLE="Atlas AI API"`、`DESCRIPTION="模块化架构接口文档"`、`VERSION="1.0.0"`。 |
| `logging_config.py` | 日志与请求上下文（`request_id`）的集中配置：`request_id_var`（`ContextVar`）、`RequestIdFilter`（把 contextvar 注入每条日志）、root logger 初始化（仅在尚未配置时）、统一 `logger = logging.getLogger("app")`。供中间件、异常处理器、日志测试接口共用。 |
| `middleware.py` | HTTP 中间件：`add_request_id`（每个请求生成/透传 `request_id`，存入 `request.state` 与 `request_id_var`；异常只 `raise` 交给全局处理器，不在中间件重复打堆栈）、`request_timing_middleware`（中间件测试：统计请求耗时并打印，注册到同一个 app 实例，**绝不重建 `app`**）。 |
| `exception_handlers.py` | 异常处理器：`device_not_found_handler`（`DeviceNotFoundError` → 404 JSON）、`global_exception_handler`（兜底捕获所有 `Exception`，统一返回 500 JSON 并带 `request_id`，**阻止 uvicorn 打印原生 ASGI 堆栈**；`HTTPException` 仍由 Starlette 默认处理器接管）。 |

### `backend/app/models/`（SQLAlchemy ORM 层）
| 文件 | 功能 |
|---|---|
| `__init__.py` | 定义 `Base = declarative_base()`（所有 ORM 模型的基类），并导入导出 `Device`，使 `from app.models import Base, Device` 可用。 |
| `device.py` | `Device` 模型，映射 `devices` 表：`id`(自增主键)、`name`、`device_type`、`ip` 三列，全部 `Mapped`/`mapped_column` 写法（SQLAlchemy 2.0 风格）。 |

### `backend/app/schemas/`（Pydantic 数据层）
| 文件 | 功能 |
|---|---|
| `__init__.py` | 导出 `DeviceCreate`、`DeviceUpdate`、`DeviceResponse`。 |
| `device.py` | `DeviceType` 枚举（`router`/`switch`/`camera`）、`name_not_blank` 校验器、`DeviceCreate`/`DeviceUpdate`/`DeviceResponse` 三个模型（`ip` 用 `IPvAnyAddress` 校验，`name` 非空）。 |

### `backend/app/services/`（业务逻辑层）
| 文件 | 功能 |
|---|---|
| `__init__.py` | 导出 `device_service` 的 5 个函数。 |
| `device_service.py` | 设备业务逻辑：**当前为内存版**（`_devices` 列表 + `_next_id` 自增），提供 `list_devices/get_device/create_device/update_device/delete_device`；另含 `calculate_total`、`group_devices`、`filter_alarm_devices` 等工具函数（教学用）。**尚未接入 `get_db` 落库**——这是下一步练习点。 |

### `backend/docs/`
| 文件 | 功能 |
|---|---|
| `Day9-Dependency-Injection.md` | Day9 依赖注入学习笔记，系统讲解 `Depends()`、`get_db()`（每请求一个 Session 的必要性）、`get_current_user()` 假用户、`require_admin()` 嵌套依赖，并配套演示运行命令与自测清单。 |

---

## 四、主要源代码文件完整内容（含关键注释）

> 以下为真实文件内容的完整转录，保留原注释。代码块使用语言标注便于阅读。

### 4.1 配置文件

#### `backend/pyproject.toml`
```toml
[project]
name = "backend"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
authors = [
    { name = "yyx", email = "yyx3112164@qq.com" }
]
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.141.1",
    "httpx>=0.28.1",
    "sqlalchemy>=2.0.54",
    "tenacity>=9.1.4",
]

[build-system]
requires = ["uv_build>=0.12.6,<0.13.0"]
build-backend = "uv_build"

# The importable package is the `app/` directory at the project root (flat layout),
# but the project name is `backend`. Tell uv_build where the module actually lives
# instead of letting it look for `src/backend/` (which we removed).
[tool.uv.build-backend]
module-name = "app"
module-root = ""
```
> **关键注释**：`project.name` 是 `backend`，但可导入源码目录是 `app/`（flat 布局）。`uv_build` 默认按项目名去 `src/backend/` 找包，这里用 `[tool.uv.build-backend]` 的 `module-name="app"` + `module-root=""` 显式指定，避免 `uv build` 报 `Expected a Python module at: src\backend\__init__.py`。

#### `backend/.gitignore`
```gitignore
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv/

# Environment variables
.env
*.env

# Logs
*.log

# Local databases
app.db
*.sqlite
*.sqlite3
```

#### `atlas-ai/.gitignore`（根级）
```gitignore
# ---- Python ----
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# ---- Virtual environment ----
.venv/
venv/
env/

# ---- WorkBuddy project memory (not source) ----
.workbuddy/

# ---- IDE ----
.idea/
.vscode/

# ---- OS ----
.DS_Store
Thumbs.db
```

#### `backend/.python-version`
```
3.12
```
> `uv` 用的 Python 版本标记，内容为 `3.12`。

#### `backend/uv.lock`（节选说明）
> 自动生成，记录完整依赖解析结果。核心直接依赖的解析版本（示例，实际以文件为准）：
> - `fastapi` → `0.141.1`（含 `starlette`、`pydantic` 等）
> - `sqlalchemy` → `2.0.54`
> - `httpx` → `0.28.1`（依赖 `httpcore`、`h11`）
> - `tenacity` → `9.1.4`
> 传递依赖含 `uvicorn`、`anyio`、`click`、`sniffio`、`idna`、`certifi` 等。该文件**不应手工编辑**，由 `uv add` / `uv lock` 维护。

---

### 4.2 入口文件

#### `backend/app/main.py`（完整内容 · 重构后“纯装配”版本）
```python
"""应用入口：只负责“装配” FastAPI 应用。

具体逻辑已抽离到独立模块，保持单一职责：
- app.core.config              应用元数据配置
- app.core.logging_config     日志与 request_id 上下文
- app.core.middleware          请求级中间件（含中间件测试）
- app.core.exception_handlers 异常处理器
- app.api.router.register_routes 路由聚合挂载

关键修复：原 main.py 末尾的“# ========== 中间件测试 ==========”片段里误写了
`app = FastAPI(title="Middleware Demo")`，重新创建了一个 FastAPI 实例，
把前面已挂载的全部路由 / 中间件 / 异常处理器全部覆盖掉了，导致 /docs 只剩
该片段里的 GET /devices 和 GET /。本版本不再重建 app，中间件统一注册到
“同一个” app 实例上，所有路由都能正确注册并显示在 /docs。
"""
from fastapi import FastAPI

from app.api.router import register_routes
from app.core.config import DESCRIPTION, TITLE, VERSION
from app.core.exception_handlers import device_not_found_handler, global_exception_handler
from app.core.exceptions import DeviceNotFoundError
from app.core.middleware import add_request_id, request_timing_middleware

# 1) 创建应用（全工程只此一处）
app = FastAPI(title=TITLE, description=DESCRIPTION, version=VERSION)

# 2) 注册路由（尽早执行，确保即使后续中间件 / 处理器有问题，路由也已挂载）
register_routes(app)

# 3) 注册中间件
# 请求 id 注入（内层，紧贴端点）
app.middleware("http")(add_request_id)

# ========== 中间件测试 ==========
# 测试用中间件：统计请求耗时并打印，验证中间件链正常。
# 注册到“同一个 app 实例”，绝不再写 app = FastAPI(...) 覆盖应用。
app.middleware("http")(request_timing_middleware)

# 4) 注册异常处理器
app.add_exception_handler(DeviceNotFoundError, device_not_found_handler)
app.add_exception_handler(Exception, global_exception_handler)
```
> **关键注释**：
> - 整个 `main.py` 现在只有“装配”职责：创建**唯一** `app` 实例 → `register_routes(app)` → 注册两个中间件 → 注册两个异常处理器。**绝不在本文件内联业务/配置/日志/中间件代码**。
> - 历史上 `/docs` 曾“只剩 2 个接口”的 bug，根因就是某段“中间件测试”代码里误写 `app = FastAPI(...)` 重建了实例，覆盖了前面已挂载的全部路由；本版本已消除该隐患（见 `middleware.py` 注释）。
> - 路由、中间件、异常处理器的真实实现分别在 `app/api/router.py`、`app/core/middleware.py`、`app/core/exception_handlers.py`。

#### `backend/app/core/config.py`（完整内容）
```python
"""应用配置：集中管理 FastAPI 实例的元数据。

原本这些 title/description/version 直接写死在 main.py 里，现抽离到此处，
便于按环境统一管理，main.py 只负责装配。
"""
TITLE = "Atlas AI API"
DESCRIPTION = "模块化架构接口文档"
VERSION = "1.0.0"
```

#### `backend/app/core/logging_config.py`（完整内容）
```python
"""日志与请求上下文（request_id）的集中配置。

原本这些定义散落在 main.py，现抽离到此处，供中间件、全局异常处理器、
日志测试接口等模块共用，避免重复定义与日志格式被覆盖。
"""
import logging
import sys
from contextvars import ContextVar

# 上下文变量：保存当前请求的 request_id，每个请求独立
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# 自定义日志格式：timestamp level request_id module message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s"


class RequestIdFilter(logging.Filter):
    """把 contextvar 里的 request_id 注入到每条日志记录。"""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


# 配置 root logger（仅当尚未配置时生效，避免重复添加 handler）
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# 全局统一 logger，供各模块直接 import 使用
logger = logging.getLogger("app")
if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
    logger.addFilter(RequestIdFilter())
```

#### `backend/app/core/middleware.py`（完整内容）
```python
"""HTTP 中间件：请求级横切逻辑集中在此。

原本这些 @app.middleware 写在 main.py，现抽离为独立函数，
在 main.py 里用 app.middleware("http")(func) 注册到“同一个” app 实例上。
"""
import time
import uuid

from fastapi import Request

from app.core.logging_config import logger, request_id_var


async def add_request_id(request: Request, call_next):
    """为每个请求生成/透传 request_id，并注入日志上下文。"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    # 同时存到 request.state：异常处理器在 finally(reset) 之后才执行，
    # 直接读 contextvar 会得到空值，从 request.state 读则稳定。
    request.state.request_id = request_id
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        # 不在中间件里重复打堆栈：异常交给全局异常处理器统一记录
        raise exc
    finally:
        request_id_var.reset(token)


async def request_timing_middleware(request: Request, call_next):
    """中间件测试：统计请求耗时并打印，验证中间件链正常工作。

    对应原 main.py “# ========== 中间件测试 ==========”片段中的
    request_timing_middleware。原片段误用了 `app = FastAPI(...)`
    重新创建实例，导致先前挂载的全部路由丢失——这里改为注册到同一个 app 上。
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000)
    # add_request_id 同时把 request_id 写入 request.state 与 request_id_var；
    # 同步端点经线程池执行时 contextvar 传递偶有不一致，这里两者取其一，保证日志稳定带 id。
    req_id = getattr(request.state, "request_id", "") or request_id_var.get()
    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {duration_ms}ms request_id={req_id}"
    )
    return response
```

#### `backend/app/core/exception_handlers.py`（完整内容）
```python
"""全局 / 专用异常处理器。"""
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DeviceNotFoundError
from app.core.logging_config import logger, request_id_var


async def device_not_found_handler(request: Request, exc: DeviceNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def global_exception_handler(request: Request, exc: Exception):
    """兜底捕获所有未被更具体处理器拦截的异常（如 ZeroDivisionError）。

    - 统一返回 JSON 500（而不是把异常抛给 uvicorn）；
    - 用带 request_id 的日志格式记录堆栈；
    - 阻止 uvicorn 再打印那一长串原生 ASGI Traceback。
    注意：HTTPException(404/422/502/504) 由 Starlette 默认处理器接管，不受影响。
    """
    request_id = getattr(request.state, "request_id", "")
    # RequestIdFilter 从 request_id_var 读 request_id；中间件 finally 已 reset，
    # 这里临时再 set 一次，保证本处理器的日志也带正确的 request_id。
    token = request_id_var.set(request_id)
    try:
        logger.error("未处理异常已统一捕获", exc_info=exc)
    finally:
        request_id_var.reset(token)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "request_id": request_id},
    )
```

#### `backend/app/api/router.py`（完整内容）
```python
"""路由聚合：把各业务 router 统一挂载到 app。

原本这些 include_router 散落在 main.py，现集中到这里，保持 main.py 只做“装配”。
"""
from fastapi import FastAPI

from app.api.routes import demo_router, devices_router, health_router, users_router
from app.api.routes import protected


def register_routes(app: FastAPI) -> None:
    """集中注册所有子路由。

    注意：devices 只注册一次（devices_router 来自 routes/__init__ 聚合），
    避免原来 main.py 中 devices.router 与 devices_router 重复 include。
    """
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(devices_router)
    app.include_router(protected.router)
    app.include_router(demo_router)
```

#### `backend/app/api/routes/demo.py`（完整内容）
```python
"""演示 / 实验路由：根路由、外部接口调用、日志测试。

这些原本内联在 main.py，现抽离为独立 router，保持 main.py 精简。
"""
import httpx
from fastapi import APIRouter, HTTPException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.core.logging_config import logger, request_id_var

router = APIRouter(tags=["演示 / 实验"])


@router.get("/", include_in_schema=False)
def root():
    return {"message": "Welcome to Atlas AI API. Visit /docs for OpenAPI documentation."}


# ========== 外部接口调用（httpx + tenacity 重试） ==========
@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(0.5),
    retry=retry_if_exception_type(httpx.TimeoutException),
)
async def call_external_api() -> dict:
    timeout = httpx.Timeout(2.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # 该接口故意延迟 3 秒返回，用于测试超时与重试
        resp = await client.get("https://httpbin.org/delay/3")
        resp.raise_for_status()
        return resp.json()


@router.get("/external/test")
async def external_test():
    try:
        data = await call_external_api()
        return {"msg": "调用外部接口成功", "external_data": data}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="外部接口调用超时，重试后依然失败")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"外部接口错误码：{e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"网络异常：{str(e)}")


# ========== 日志测试接口 ==========
@router.get("/log-test")
def log_test():
    logger.info("这是 INFO 日志：正常业务消息")
    logger.warning("这是 WARNING 日志：警告，非阻断")
    logger.error("这是 ERROR 日志：发生错误")
    return {"msg": "查看控制台日志", "request_id": request_id_var.get()}


@router.get("/log-error")
def log_error_demo():
    try:
        1 / 0
    except Exception as e:
        logger.error("业务发生除零异常", exc_info=True)
        raise e
```

> **关键注释（重构要点）**：
> - 路由挂载全部集中在 `app/api/router.py:register_routes`，`/health`、`/users`、`/devices`、`/me`、`/external/test`、`/log-test`、`/log-error` 均无 `/api` 前缀。
> - 全局异常处理器 `global_exception_handler` 兜住所有未捕获异常，避免 uvicorn 打印原生 ASGI 堆栈；它从 `request.state.request_id` 读取 id，并临时 `request_id_var.set` 让日志带正确 id。
> - 中间件 `add_request_id` 同时把 `request_id` 存进 `request.state`（因为 `finally` 里 `request_id_var.reset` 会在异常处理器执行前重置 contextvar）。
> - `/external/test` 用 tenacity 重试 httpx 超时（目标 `httpbin.org/delay/3` 故意延迟 3 秒，超过 2 秒超时 → 重试 2 次后抛 504）。
> - 日志统一经 `app.core.logging_config.logger`，格式为 `时间 | 级别 | request_id | 模块 | 消息`。

---

### 4.3 核心逻辑

#### `backend/app/database.py`（完整内容）
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base


DATABASE_URL = "sqlite:///./app.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

# 学习阶段：应用启动时自动建表。
# 生产环境请改用 Alembic 做数据库迁移，不要依赖 create_all。
Base.metadata.create_all(bind=engine)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Session:
    """依赖：每个请求创建一个 Session，请求结束后自动关闭。

    用 yield 让 FastAPI 在请求结束时执行 finally 里的 db.close()，
    把数据库连接归还给连接池，避免连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
> **关键注释**：`get_db` 用 `yield` + `finally` 实现「每请求一个 Session、用完即还」，是 FastAPI + SQLAlchemy 的标准写法，避免连接池耗尽（`QueuePool overflow`）。

#### `backend/app/dependencies.py`（完整内容）
```python
"""FastAPI 依赖（Dependency Injection）示例。

Day 9 学习重点：
- get_current_user()：先写“假用户”，后续再替换为真实 JWT 校验。
- get_db()：见 app/database.py（每个请求一个 Session）。
- require_admin()：演示依赖可以“依赖另一个依赖”。
"""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel


class User(BaseModel):
    """当前登录用户模型。

    真实项目里通常会把它挪到 app/schemas/user.py，这里为教学自包含放在 dependencies 里。
    """

    id: int
    username: str
    is_active: bool = True
    is_admin: bool = False


# 学习阶段：写死的“假用户”。真实场景应根据 Token 查库得到。
FAKE_USER = User(id=1, username="yyx", is_active=True, is_admin=True)


def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> User:
    """依赖：返回“当前登录用户”。

    现在只是假实现——直接返回一个写死的用户。
    后续你要做的真实版本：
      1. 从 Authorization 头取出 Bearer Token；
      2. 用 jwt 解码 / 校验签名；
      3. 用 Token 里的 user_id 去数据库查用户；
      4. 查不到或已禁用就 raise HTTPException(401)。
    """
    # 如果前端带了 X-User-Id，就假装他是那个用户（仅演示）。
    if x_user_id is None:
        return FAKE_USER
    return User(id=x_user_id, username=f"user-{x_user_id}", is_active=True)


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """依赖的嵌套：它自己又依赖 get_current_user。

    FastAPI 会自动先解析 get_current_user，把结果注入到这里，
    再执行本函数做“是否管理员”的二次校验。
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
```

#### `backend/app/core/exceptions.py`（完整内容）
```python
class DeviceNotFoundError(Exception):
    """设备不存在"""
    pass
```

---

### 4.4 路由层

#### `backend/app/api/routes/__init__.py`
```python
from .demo import router as demo_router
from .devices import router as devices_router
from .health import router as health_router
from .users import router as users_router

__all__ = ["demo_router", "health_router", "users_router", "devices_router"]
```

#### `backend/app/api/routes/health.py`
```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["系统运维"]
)

@router.get("", summary="健康检查接口")
def check_health():
    return {"status": "healthy", "database": "connected"}
```

#### `backend/app/api/routes/devices.py`
```python
from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.services.device_service import get_device
from app.core.exceptions import DeviceNotFoundError
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.services import device_service

# 路由级依赖函数：校验请求头 Token
def verify_device_token(x_device_token: str = Header("default-token")):
    if x_device_token != "secret-device-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Device Token"
        )

router = APIRouter(
    prefix="/devices",
    tags=["设备管理"],
    dependencies=[Depends(verify_device_token)]  # 此路由下的所有接口都会触发 token 校验
)
@router.get("", response_model=list[DeviceResponse])
def list_devices():
    return device_service.list_devices()


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: int):
    device = device_service.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(data: DeviceCreate):
    return device_service.create_device(data)


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, data: DeviceUpdate):
    device = device_service.update_device(device_id, data)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int):
    ok = device_service.delete_device(device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="设备不存在")
    return None
```
> **关键注释**：`Depends(verify_device_token)` 挂在整条 `router` 上，意味着 `/devices` 下所有接口都要求请求头 `X-Device-Token: secret-device-key`，否则 401。注意 `device_service.list_devices()` 等当前返回**内存假数据**，尚未真正查 `Device` 表。

#### `backend/app/api/routes/users.py`
```python
from fastapi import APIRouter, HTTPException, status

router = APIRouter(
    prefix="/users",
    tags=["用户管理"]
)

# 模拟数据
FAKE_USERS = [
    {"id": 1, "username": "alex", "role": "admin"},
    {"id": 2, "username": "dev_user", "role": "developer"}
]

@router.get("", summary="获取用户列表")
def get_users():
    return FAKE_USERS

@router.get("/{user_id}", summary="获取指定用户")
def get_user(user_id: int):
    for user in FAKE_USERS:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
```

#### `backend/app/api/routes/protected.py`
```python
"""演示路由：把 Day9 的两个依赖用起来。

运行后访问 /docs 能看到：
- GET /me           → 注入当前用户（假用户）
- GET /me/admin     → 要求管理员（嵌套依赖）
- GET /me/ping-db   → 注入数据库 Session 并验证可用
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import User, get_current_user, require_admin

router = APIRouter(prefix="/me", tags=["当前用户（演示 DI）"])

# 用 Annotated 把“类型 + 依赖”打包，端点签名更干净（推荐写法）。
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("")
def read_me(user: CurrentUser):
    """当前登录用户。依赖 get_current_user 自动注入 user。"""
    return user


@router.get("/admin")
def read_admin(user: Annotated[User, Depends(require_admin)]):
    """只有管理员能访问：require_admin 内部又依赖 get_current_user。"""
    return {"message": f"你好，管理员 {user.username}"}


@router.get("/ping-db")
def ping_db(db: DbSession):
    """演示：数据库 Session 通过 get_db 注入，而不是在接口里自己 new。

    真实场景里你会写 db.query(Device).all() 之类；这里只验证 session 可用。
    """
    return {
        "db_state": "Session 已注入且可用",
        "in_transaction": db.in_transaction(),
    }
```

---

### 4.5 模型层（SQLAlchemy ORM）

#### `backend/app/models/__init__.py`
```python
"""SQLAlchemy ORM 模型包。

所有数据库表模型都继承这里的 Base。
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.device import Device  # noqa: E402,F401

__all__ = ["Base", "Device"]
```

#### `backend/app/models/device.py`
```python
"""设备表 ORM 模型。

与 schemas/device.py 的 Pydantic 模型对应：
- schemas.DeviceCreate    -> 创建请求体
- schemas.DeviceResponse  -> 返回响应
- models.Device          -> 数据库表（这一张）
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
```

---

### 4.6 Schema 层（Pydantic）

#### `backend/app/schemas/__init__.py`
```python
"""请求 / 返回的数据格式（Pydantic 模型）。"""
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate

__all__ = ["DeviceCreate", "DeviceUpdate", "DeviceResponse"]
```

#### `backend/app/schemas/device.py`
```python
from enum import Enum
from pydantic import BaseModel, Field, IPvAnyAddress, field_validator

class DeviceType(str, Enum):
    router = "router"
    switch = "switch"
    camera = "camera"
@field_validator("name")
@classmethod
def name_not_blank(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("name 不能为空")
    return v.strip()

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, description="设备名称，不能为空")
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
> **关键注释**：`DeviceType` 是枚举，`device_type` 只能取 `router`/`switch`/`camera`，否则 `422`；`ip` 用 `IPvAnyAddress` 校验为合法 IP；`name` 非空。

---

### 4.7 服务层（业务逻辑）

#### `backend/app/services/__init__.py`
```python
"""业务逻辑层。"""
from app.services.device_service import (
    create_device,
    delete_device,
    get_device,
    list_devices,
    update_device,
)

__all__ = [
    "list_devices",
    "get_device",
    "create_device",
    "update_device",
    "delete_device",
]
```

#### `backend/app/services/device_service.py`（完整内容）
```python
from app.schemas.device import DeviceCreate, DeviceUpdate

_devices: list[dict] = []
_next_id = 1
def calculate_total(prices: list[float]) -> float:
    return sum(prices)

def group_devices(devices: list[dict]) -> dict[str, list[dict]]:
    groups = {}
    for device in devices:
        group_name = device["group"]
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append(device)
    return groups

def filter_alarm_devices(
    devices: list[dict],
    level: str = "critical"
) -> list[dict]:
    return [device for device in devices if device.get("level") == level]
def list_devices() -> list[dict]:
    return _devices
def get_device(device_id: int) -> dict | None:
    for device in _devices:
        if device["id"] == device_id:
            return device
    return None

def create_device(data: DeviceCreate) -> dict:
    global _next_id
    device = {
        "id": _next_id,
        **data.model_dump(mode="json"),
    }
    _next_id += 1
    _devices.append(device)
    return device


def update_device(device_id: int, data: DeviceUpdate) -> dict | None:
    device = get_device(device_id)
    if device is None:
        return None

    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )
    device.update(update_data)
    return device


def delete_device(device_id: int) -> bool:
    device = get_device(device_id)
    if device is None:
        return False
    _devices.remove(device)
    return True
```
> **关键注释**：当前 `device_service` 全部基于**进程内内存列表** `_devices`，**没有**使用 `get_db` 连接数据库。要让 `routes→schemas→services→models→DB` 真正打通，应把这里 5 个 CRUD 函数改为接收 `db: Session = Depends(get_db)` 并操作 `Device` 表（这是项目下一步练习）。`calculate_total/group_devices/filter_alarm_devices` 是额外教学工具函数，未被路由调用。

---

### 4.8 学习文档

#### `backend/docs/Day9-Dependency-Injection.md`（完整内容）
````markdown
# Day 9 · FastAPI 依赖注入（Dependency Injection）

> 配套代码已写入你的工程（可直接运行）：
> - `backend/app/database.py` → 新增 `get_db()`
> - `backend/app/dependencies.py` → 新增 `get_current_user()`（假用户）、`require_admin()`
> - `backend/app/api/routes/protected.py` → 演示路由 `/me`、`/me/admin`、`/me/ping-db`
> - `backend/app/main.py` → 已挂载上面的路由
> - 依赖 `sqlalchemy>=2.0.54` 已通过 `uv add` 安装

## 0. 一句话目标

学会用 `Depends()` 把「当前登录用户」和「数据库 Session」做成**可复用、可注入、可替换**的依赖；并真正理解**为什么不该在每个接口里自己 `new` 一个 Session**。

## 1. 什么是依赖注入（DI）

**没有 DI 的写法（直觉写法）：**

```python
@app.get("/me")
def me():
    db = SessionLocal()          # 每个接口都自己造
    user = get_current_user()    # 每个接口都自己调
    try:
        ...
    finally:
        db.close()               # 还容易忘记关
```

问题：

- 重复：10 个接口写 10 遍。
- 难测试：想换成测试库？得改 10 个地方。
- 生命周期混乱：谁负责关连接？忘了就泄漏。

**DI 的写法：**

```python
@app.get("/me")
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ...
```

你只**声明需要什么**（`db`、`user`），FastAPI 负责**怎么造、何时造、何时销毁**。函数 `get_db` / `get_current_user` 就叫「依赖」。

你的工程里 `app/api/routes/devices.py` 其实早就用过了——`verify_device_token` 就是个依赖，而且挂在整条路由上：

```python
router = APIRouter(prefix="/devices", dependencies=[Depends(verify_device_token)])
```

所以 Day 9 不是从零学，是把你已经会的一点系统化。

## 2. Depends() 怎么运转

要点：

- 依赖可以是**普通函数**，返回值会被注入到对应参数。
- 依赖参数也能**再依赖别的依赖**（嵌套）。
- 用 `yield` 的依赖，FastAPI 会在请求结束后执行 `yield` 之后的代码（用来做清理，比如 `db.close()`）。

## 3. 实战①：get_db() —— 每个请求一个 Session

`backend/app/database.py`（节选）：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db          # 把 Session 交给接口用
    finally:
        db.close()        # 请求结束，归还连接
```

## 4. 核心目标：为什么 Session 不该每个接口自己 new

这是今天最重要的结论。先看清两个**常见误区**：

### 误区 A：全局复用一个 Session（跨请求共享）

```python
# 千万别这么做
db = SessionLocal()   # 模块级全局变量

@app.get("/a")
def a():
    return db.query(...)   # 请求1用它
@app.get("/b")
def b():
    return db.query(...)   # 请求2也用它
```

`Session` **不是线程安全的**。FastAPI 默认用线程池跑同步接口，并发请求会同时碰同一个 Session → 数据错乱、幽灵提交、`Session is already flushed` 之类的诡异报错。

### 误区 B：每个接口自己 new 但忘了关

```python
@app.get("/x")
def x():
    db = SessionLocal()   # new 了一个
    return db.query(...)  # 用完没 close
```

每个 `SessionLocal()` 会向连接池**借一条数据库连接**，只有 `close()` 才归还。你借了不还会怎样？

- 连接池大小有限（SQLAlchemy 默认 5 条 + 少量溢出）。
- 请求多了，池被借光 → 新请求阻塞等待 → 最终 `TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out`。
- 这就是「连接泄漏」。

### 正解：每请求一个 Session，用完即还（get_db 做的事）

把 Session 的「造」和「毁」集中到一个 `yield` 依赖里：

- 每个请求得到**自己专属**的 Session（线程安全 ✓）。
- 请求结束 `finally: db.close()` 把连接**归还**给池（不泄漏 ✓）。
- 事务边界自然对齐「一次 HTTP 请求 = 一个工作单元」（✓）。
- 测试时只需 `app.dependency_overrides[get_db] = 我的测试依赖`，就能换成内存 SQLite（✓ 可测试）。

一句话记忆：**Session 要「短命、私有、自动回收」，不要「长寿共享」也不要「随手 new 随手丢」。**

## 5. 实战②：get_current_user() —— 先写假用户

`backend/app/dependencies.py`：

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    is_active: bool = True
    is_admin: bool = False

FAKE_USER = User(id=1, username="yyx", is_active=True, is_admin=True)

def get_current_user(x_user_id: int | None = Header(default=None, alias="X-User-Id")) -> User:
    # 学习阶段：直接返回假用户
    if x_user_id is None:
        return FAKE_USER
    return User(id=x_user_id, username=f"user-{x_user_id}", is_active=True)

def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
```

注意 `require_admin` **依赖 `get_current_user`**——这就是依赖嵌套。FastAPI 会先解析内层，把结果注入外层，再跑外层校验。

真实项目里 `get_current_user` 应改成：从 `Authorization` 头取 Bearer Token → 验签 → 用里面的 user_id 查库 → 查不到/禁用就 `raise 401`。现在先写死，把 DI 的机制练熟。

## 6. 把依赖用起来

`backend/app/api/routes/protected.py`：

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import User, get_current_user, require_admin

router = APIRouter(prefix="/me", tags=["当前用户（演示 DI）"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("")
def read_me(user: CurrentUser):
    return user

@router.get("/admin")
def read_admin(user: Annotated[User, Depends(require_admin)]):
    return {"message": f"你好，管理员 {user.username}"}

@router.get("/ping-db")
def ping_db(db: DbSession):
    return {"db_state": "Session 已注入且可用", "in_transaction": db.in_transaction()}
```

`Annotated[Session, Depends(get_db)]` 是推荐写法：把「类型 + 依赖」打包成一个别名，接口签名既干净又有类型提示。

## 7. 跑起来验证

```bash
cd E:/Codes/atlas-ai/backend
uv run uvicorn app.main:app --reload
```

打开 http://127.0.0.1:8000/docs ：

- `GET /me` → 直接返回假用户 `{"id":1,"username":"yyx",...}`。
- `GET /me/admin` → 因为假用户是管理员，返回成功；把 `FAKE_USER` 的 `is_admin` 改成 `False` 再试，会得到 403。
- `GET /me/ping-db` → 返回 `{"db_state":"Session 已注入且可用","in_transaction":false}`，证明 `get_db` 真的把 Session 注入了。

## 8. 检查清单（学完自测）

- [ ] 能说出 `Depends()` 把「造对象」和「用对象」分开了。
- [ ] 能解释为什么全局共享一个 Session 会出线程安全问题。
- [ ] 能解释为什么 new 了不 close 会导致连接池耗尽（`QueuePool overflow`）。
- [ ] 知道 `get_db` 用 `yield` + `finally` 实现「每请求一个、用完即还」。
- [ ] 能写一个嵌套依赖（如 `require_admin` 依赖 `get_current_user`）。
- [ ] 知道怎么用 `app.dependency_overrides` 在测试里替换 `get_db`。

## 9. 下一步

- 把 `get_current_user` 换成真实 JWT 校验（引入 `python-jose` + `passlib`）。
- 给 `get_db` 加上异常时 `db.rollback()` 的兜底。
- 学 `BackgroundTasks`、`Request`、`Response` 这些内置依赖。
````

---

## 五、运行方式与已验证结果

### 启动命令
```bash
cd E:/Codes/atlas-ai/backend
uv run fastapi dev ./app/main.py
# 或
uv run uvicorn app.main:app --reload
```
> 访问 `http://127.0.0.1:8000/docs` 查看交互式 Swagger 文档。

### 已实测通过的接口（TestClient 验证）
> 重构后 `GET /docs`（OpenAPI）共声明 **11** 个接口：`/devices`(GET,POST)、`/devices/{device_id}`(DELETE,GET,PUT)、`/external/test`、`/health`、`/log-error`、`/log-test`、`/me`、`/me/admin`、`/me/ping-db`、`/users`、`/users/{user_id}`。以下为冒烟结果：

| 请求 | 结果 | 说明 |
|---|---|---|
| `GET /` | 200 | 根路由（位于 `demo.py`） |
| `GET /health` | 200 | 健康检查 |
| `GET /users` | 200 | 用户假数据 |
| `GET /me`（无头 → 假用户 `yyx`） | 200 | DI：`get_current_user` |
| `GET /me/admin` | 200 | 嵌套依赖：`require_admin` |
| `GET /me/ping-db` | 200，`Session 已注入且可用` | DI：`get_db`，建表已生效 |
| `GET /devices`（无 token） | 401 | 设备 token 守卫 |
| `GET /devices`（token=`secret-device-key`） | 200 `[]` | token 通过，内存 service 返回空列表 |
| `POST /devices` 填 `"device_type":"panel"` | 422 | schema 枚举校验生效（`panel` 不在 `router/switch/camera`） |
| `GET /external/test` | 504（httpbin 延迟 3s 超 2s 超时，tenacity 重试 2 次后仍失败） | httpx + tenacity 重试演示 |
| `GET /log-test` | 200 | 三类日志（INFO/WARNING/ERROR）+ request_id 正确 |
| `GET /log-error` | 500 JSON（无原生 ASGI 堆栈） | 全局异常处理器生效 |

### 注意事项 / 已知坑
1. **路由无 `/api` 前缀**：实测路径是 `/health`、`/devices`、`/me`、`/users`，不是 `/api/...`。
2. **`uv_build` 包指向**：`pyproject.toml` 必须保留 `[tool.uv.build-backend]` 配置，否则 `uv run` 报 `Expected a Python module at: src\backend\__init__.py`。
3. **`services` 未接 DB**：`GET/POST /devices` 返回的是内存假数据，`Device` ORM 模型目前仅被 `create_all` 建表、尚未被 service 读写（下一步打通）。
4. **两个 `app.db`**：根目录与 `backend/` 各可能有一个；当前 `DATABASE_URL="sqlite:///./app.db"` 指向**运行目录**（从 `backend/` 启动即 `backend/app.db`）。
5. **`POST /devices` 的 `device_type`** 必须是枚举值 `router`/`switch`/`camera`，`ip` 必须是合法 IP 地址。
6. **`/docs` 接口丢失 bug（已修复）**：曾在 `main.py` 末尾某段“中间件测试”代码里误写 `app = FastAPI(title="Middleware Demo")`，重建了 app 实例，覆盖掉前面已挂载的全部路由，导致 `/docs` 只剩 `/devices` 与 `/` 两个接口。现已把 `main.py` 重构为“纯装配”并抽离出 `core/`（config/logging_config/middleware/exception_handlers）与 `api/router.py`/`api/routes/demo.py`，且**全工程只创建一次 `app`**，杜绝重建；实测 `/docs` 恢复显示全部 11 个接口。

---

## 六、遗留问题与下一步建议

1. **打通数据库全链路**：把 `app/services/device_service.py` 的 5 个 CRUD 函数改为接收 `db: Session = Depends(get_db)`，直接读写 `Device` 表，让 `routes→schemas→services→models→DB` 真正闭环。
2. **真实鉴权**：将 `get_current_user` 从假用户改为 JWT 校验（引入 `python-jose` + `passlib`），`require_admin` 随之生效。
3. **数据库迁移**：用 Alembic 替代 `create_all` 管理表结构变更（生产必备）。
4. **`get_db` 健壮性**：在 `get_db` 的 `except` 中加 `db.rollback()` 兜底，避免异常事务悬挂。
5. **补充 `README.md`**：当前 `backend/README.md` 为空，建议写入启动、接口、架构说明（本文件可作为素材）。
6. **`/log-error` 日志收敛（可选）**：目前异常会打两条日志（路由内 + 全局处理器）；若只要一条，可让路由捕获后不再 `raise`，或全局处理器不打印 `exc_info`。
