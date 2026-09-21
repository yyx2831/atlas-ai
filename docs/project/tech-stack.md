# 技术栈（tech-stack）

| 类别 | 选型 | 版本 / 说明 | 在工程中何处声明 |
|---|---|---|---|
| 语言 | Python | `requires-python = ">=3.12"`；`.python-version = 3.12` | `backend/pyproject.toml`、`backend/.python-version` |
| 包管理 | **uv** | 锁定依赖在 `backend/uv.lock` | `backend/pyproject.toml` 的 `[build-system]`（`uv_build`） |
| Web 框架 | **FastAPI** | `fastapi[standard]>=0.141.1`（含 uvicorn/Starlette） | `pyproject.toml` dependencies |
| ORM | **SQLAlchemy 2.0** | `sqlalchemy>=2.0.54`；使用 `Mapped` / `mapped_column` 2.0 风格 | `pyproject.toml`；`app/models/device.py`、`app/database.py` |
| 数据校验 | **Pydantic v2** | 随 FastAPI 引入；`Field`、`field_validator`、`IPvAnyAddress` | `app/schemas/device.py` |
| 数据库 | **SQLite / PostgreSQL** | 默认固定 backend/app.db；DATABASE_URL 可切到 PostgreSQL + psycopg 3 | `app/database.py` |
| HTTP 客户端 | **httpx** | `httpx>=0.28.1`；异步 `AsyncClient` | `pyproject.toml`；`app/api/routes/demo.py` |
| 重试 | **tenacity** | `tenacity>=9.1.4`；`@retry` 装饰器 | `pyproject.toml`；`app/api/routes/demo.py` |
| 服务器 | **uvicorn** | 由 `fastapi[standard]` 提供；`fastapi dev` 内部调用 | 运行时 |
| 文档生成 | OpenAPI / Swagger | FastAPI 自带 `/docs`（Swagger UI）、`/redoc`、`/openapi.json` | 框架内置 |

## 构建后端（重要）

- 构建后端是 **`uv_build`**（非 setuptools / hatch）。
- 工程名 `name = "backend"`，但可导入包是 `app/`（flat layout）。
- 因此 `pyproject.toml` 必须配置：

```toml
[tool.uv.build-backend]
module-name = "app"
module-root = ""
```

否则 `uv run fastapi dev` 会报 `Expected a Python module at: src/backend/__init__.py`。

## 目录约定

- **路由无 `/api` 前缀**：`/health`、`/devices`、`/users`、`/me`、`/external/test`、`/log-test`、`/log-error` 均为根级。
- 包内导入一律用绝对导入 `from app.xxx import yyy`（`backend/app` 是包根）。
- 分层：`api/routes`（HTTP）→ `schemas`（校验）→ `services`（业务）→ `models`（ORM）↔ `database`（引擎/Session）→ `core`（横切）。
