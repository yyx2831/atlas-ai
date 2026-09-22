# 源码签名地图（repo-map）

> 本文件由脚本从 `backend/app/**/*.py` 自动抽取（类/函数签名、导入、导出），
> 用于 Agent 快速建立「有哪些文件、有哪些可调用符号」的心智模型。
> 重新生成：仓库根保留生成脚本 `_gen_repomap.py`，直接运行 `python _gen_repomap.py` 即可刷新本文件。

---

## `app/__init__.py`

_(无顶层类/函数)_

---

## `app/cli.py`

> 首次初始化：uv run python -m app.cli init --email you@example.com --demo。

**imports**

```
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from getpass import getpass
from sqlalchemy import select
from app.core.logging_config import logger
from app.core.settings import get_settings
from app.database import init_db, SessionLocal
from app.models import Device, Alarm
from app.models.platform import Account
from app.schemas.platform import AccountInput
from app.services.accounts import create_account
from app.services.runtime import Runtime
from app.services.knowledge import upload
```

**symbols**

```
SAMPLE_MANUAL = ...
 async def seed(db, account)
 def main()
```

---

## `app/database.py`

> Day 19/21：连接配置与每请求一个 Session；导入时不建表。

**imports**

```
from collections.abc import Iterator
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from app.models import Base
from app.core.settings import get_settings
```

**symbols**

```
DEFAULT_DB_PATH = ...
DATABASE_URL = ...
 def build_engine(url)
engine = ...
SessionLocal = ...
 def init_db(bind)
 def get_db()
```

---

## `app/dependencies.py`

> HTTP 依赖：验证签名、查账户状态、检查权限，再进入业务函数。

**imports**

```
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models.platform import Account
```

**symbols**

```
bearer = ...
DbSession = ...
 def get_current_user(db, credentials)
CurrentUser = ...
 def require_admin(user)
AdminUser = ...
 def get_runtime(request)
```

---

## `app/main.py`

> Atlas 唯一应用入口。阅读顺序：配置 → 资源生命周期 → 路由 → 中间件。

**imports**

```
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.api.router import register_routes
from app.core.settings import get_settings
from app.core.exception_handlers import global_exception_handler
from app.core.middleware import add_request_id, request_timing_middleware
from app.database import init_db, SessionLocal
from app.services.runtime import Runtime
from app.services.accounts import bootstrap_admin
from app.services.llm import ProviderError
from sqlalchemy import update
from app.models.platform import Message, AgentRun
```

**symbols**

```
@asynccontextmanager async def lifespan(app)
app = ...
@<decorator> async def provider_error(request, exc)
@<decorator> async def timeout_error(request, exc)
```

---

## `app/mcp_server.py`

> 独立 stdio MCP 服务：通过受 JWT 保护的 HTTP API 获取数据，不直连数据库。

**imports**

```
import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
```

**symbols**

```
mcp = ...
 async def request(path, params)
@<decorator> async def get_device(device_id)
@<decorator> async def get_alarm(device_id, limit)
@<decorator> async def search_manual(query)
```

---

## `app/api/__init__.py`

> API 层：HTTP 接口与路由聚合。

_(无顶层类/函数)_

---

## `app/api/router.py`

> 所有 URL 在这里集中注册；backend 无 /api 前缀，代理负责去前缀。

**imports**

```
from fastapi import FastAPI
from app.api.routes import devices, protected, auth, knowledge, chat, agent, alarms, system
```

**symbols**

```
 def register_routes(app)
```

---

## `app/api/routes/__init__.py`

**imports**

```
from demo import router
from devices import router
from health import router
from users import router
```

**symbols**

```
__all__ = ...
```

---

## `app/api/routes/agent.py`

**imports**

```
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from app.dependencies import CurrentUser, DbSession
from app.models import Device
from app.models.platform import AgentRun
from app.schemas.platform import AgentInput
from app.services.agent import run_agent
```

**symbols**

```
router = ...
@<decorator> async def run(data, request, db, user)
@<decorator> def runs(db, user)
```

---

## `app/api/routes/alarms.py`

**imports**

```
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from app.dependencies import DbSession, CurrentUser, AdminUser
from app.models import Device, Alarm
from app.schemas.platform import AlarmInput
```

**symbols**

```
router = ...
@<decorator> def get_alarms(device_id, db, user, limit)
@<decorator> def add_alarm(device_id, data, db, user)
```

---

## `app/api/routes/auth.py`

**imports**

```
from fastapi import APIRouter, Request
from sqlalchemy import select
from app.core.security import DUMMY_HASH, create_token, password_hasher
from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models.platform import Account
from app.schemas.platform import AccountInput, LoginInput
from app.services.accounts import create_account
```

**symbols**

```
router = ...
@<decorator> def login(data, request, db)
@<decorator> def me(user)
@<decorator> def add_account(data, db, admin)
@<decorator> def users(db, admin)
```

---

## `app/api/routes/chat.py`

**imports**

```
import asyncio
import json
from time import perf_counter
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from app.dependencies import CurrentUser, DbSession
from app.models.platform import Conversation, Message
from app.schemas.platform import ChatInput
from app.services import chat
from app.services.llm import ProviderError
```

**symbols**

```
router = ...
@<decorator> def conversations(db, user)
@<decorator> def history(identifier, db, user)
@<decorator> def remove(identifier, db, user)
@<decorator> async def chat(data, request, db, user)
@<decorator> async def stream(data, request, db, user)
```

---

## `app/api/routes/demo.py`

> 演示 / 实验路由：根路由、外部接口调用、日志测试。

**imports**

```
import httpx
from fastapi import APIRouter, HTTPException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed
from app.core.logging_config import logger, request_id_var
```

**symbols**

```
router = ...
@<decorator> def root()
@retry(...) async def call_external_api()
@<decorator> async def external_test()
@<decorator> def log_test()
@<decorator> def log_error_demo()
```

---

## `app/api/routes/devices.py`

**imports**

```
from typing import Annotated
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.services import device_service
from app.dependencies import get_current_user, require_admin
```

**symbols**

```
DbSession = ...
router = ...
@<decorator> def list_devices(db)
@<decorator> def get_device(device_id, db)
@<decorator> def create_device(data, db)
@<decorator> def update_device(device_id, data, db)
@<decorator> def delete_device(device_id, db)
```

---

## `app/api/routes/health.py`

**imports**

```
from fastapi import APIRouter
```

**symbols**

```
router = ...
@<decorator> def check_health()
```

---

## `app/api/routes/knowledge.py`

**imports**

```
import asyncio
from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from app.dependencies import CurrentUser, DbSession
from app.models.platform import Chunk, Document
from app.services import knowledge
```

**symbols**

```
router = ...
 def summary(document)
@<decorator> def documents(db, user)
@<decorator> async def upload(request, db, user, file, product, version)
@<decorator> def detail(identifier, db, user)
@<decorator> def original(identifier, request, db, user)
@<decorator> async def reindex(identifier, request, db, user)
@<decorator> async def remove(identifier, request, db, user)
@<decorator> async def search(request, db, user, q, top_k, product, version)
```

---

## `app/api/routes/protected.py`

> 保留 /me 学习入口，身份现在来自真实 JWT。

**imports**

```
from fastapi import APIRouter
from sqlalchemy import text
from app.dependencies import CurrentUser, AdminUser, DbSession
```

**symbols**

```
router = ...
@<decorator> def me(user)
@<decorator> def admin(user)
@<decorator> def ping_db(db, user)
```

---

## `app/api/routes/system.py`

**imports**

```
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.dependencies import DbSession, CurrentUser
```

**symbols**

```
router = ...
@<decorator> def health()
@<decorator> async def ready(request, db)
@<decorator> def info(request, user)
```

---

## `app/api/routes/users.py`

**imports**

```
from fastapi import APIRouter, HTTPException, status
```

**symbols**

```
router = ...
FAKE_USERS = ...
@<decorator> def get_users()
@<decorator> def get_user(user_id)
```

---

## `app/core/__init__.py`

> 核心基础设施：配置、异常等。

_(无顶层类/函数)_

---

## `app/core/config.py`

> 应用配置：集中管理 FastAPI 实例的元数据。

**symbols**

```
TITLE = ...
DESCRIPTION = ...
VERSION = ...
```

---

## `app/core/exception_handlers.py`

> 全局 / 专用异常处理器。

**imports**

```
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DeviceNotFoundError
from app.core.logging_config import logger, request_id_var
```

**symbols**

```
 async def device_not_found_handler(request, exc)
 async def global_exception_handler(request, exc)
```

---

## `app/core/exceptions.py`

**symbols**

```
class DeviceNotFoundError(Exception):
```

---

## `app/core/logging_config.py`

> 日志与请求上下文（request_id）的集中配置。

**imports**

```
import logging
import sys
from contextvars import ContextVar
```

**symbols**

```
LOG_FORMAT = ...
class RequestIdFilter(logging.Filter):
   def filter(self, record)
logger = ...
```

---

## `app/core/middleware.py`

> HTTP 中间件：请求级横切逻辑集中在此。

**imports**

```
import time
import uuid
from fastapi import Request
from app.core.logging_config import logger, request_id_var
```

**symbols**

```
 async def add_request_id(request, call_next)
 async def request_timing_middleware(request, call_next)
```

---

## `app/core/security.py`

> 密码只保存 Argon2 哈希；JWT 中只放身份，不相信客户端传来的角色。

**imports**

```
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.core.settings import get_settings
```

**symbols**

```
password_hasher = ...
DUMMY_HASH = ...
 def signing_key()
 def create_token(account_id)
 def decode_token(token)
```

---

## `app/core/settings.py`

> 所有可修改参数集中在这里；环境变量 > backend/.env > 默认值。

**imports**

```
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
```

**symbols**

```
BACKEND_DIR = ...
class Settings(BaseSettings):
  @model_validator(...) def validate_configuration(self)
  model_config = ...
@lru_cache def get_settings()
```

---

## `app/models/__init__.py`

> SQLAlchemy ORM 模型包。

**imports**

```
from sqlalchemy.orm import declarative_base
from app.models.device import Device
from app.models.user import User
from app.models.alarm import Alarm
from app.models.platform import Account, Document, Chunk, Conversation, Message, AgentRun
```

**symbols**

```
Base = ...
__all__ = ...
```

---

## `app/models/alarm.py`

> Day 16/19：设备一对多告警。

**imports**

```
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
```

**symbols**

```
class Alarm(Base):
  __tablename__ = ...
  __table_args__ = ...
```

---

## `app/models/device.py`

> 设备表 ORM 模型。

**imports**

```
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.models import Base
```

**symbols**

```
class Device(Base):
  __tablename__ = ...
```

---

## `app/models/platform.py`

> AI 功能的新表；保留旧 User/Device 表，避免破坏前面的学习数据。

**imports**

```
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base
```

**symbols**

```
 def now_iso()
 def new_id()
class Account(Base):
  __tablename__ = ...
class Document(Base):
  __tablename__ = ...
  __table_args__ = ...
class Chunk(Base):
  __tablename__ = ...
class Conversation(Base):
  __tablename__ = ...
class Message(Base):
  __tablename__ = ...
class AgentRun(Base):
  __tablename__ = ...
```

---

## `app/models/user.py`

> Day 19：数据库用户示例；暂不替换现有假用户认证。

**imports**

```
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base
```

**symbols**

```
class User(Base):
  __tablename__ = ...
```

---

## `app/schemas/__init__.py`

> 请求 / 返回的数据格式（Pydantic 模型）。

**imports**

```
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
```

**symbols**

```
__all__ = ...
```

---

## `app/schemas/device.py`

**imports**

```
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, field_validator
```

**symbols**

```
class DeviceType(str, Enum):
  router = ...
  switch = ...
  camera = ...
class DeviceNameValidation(BaseModel):
  @field_validator(...) @classmethod def name_not_blank(cls, value)
class DeviceCreate(DeviceNameValidation):
class DeviceUpdate(DeviceNameValidation):
class DeviceResponse(BaseModel):
  model_config = ...
```

---

## `app/schemas/platform.py`

> HTTP 输入模型：长度、范围与枚举在进入业务层之前验证。

**imports**

```
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
```

**symbols**

```
class LoginInput(BaseModel):
class AccountInput(LoginInput):
class ChatInput(BaseModel):
class AgentInput(BaseModel):
class AlarmInput(BaseModel):
class DeviceToolInput(BaseModel):
  model_config = ...
class AlarmToolInput(DeviceToolInput):
class ManualToolInput(BaseModel):
  model_config = ...
```

---

## `app/services/__init__.py`

> 业务逻辑层。

**imports**

```
from app.services.device_service import create_device, delete_device, get_device, list_devices, update_device
```

**symbols**

```
__all__ = ...
```

---

## `app/services/accounts.py`

**imports**

```
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import password_hasher
from app.models.platform import Account
from app.schemas.platform import AccountInput
```

**symbols**

```
 def create_account(db, data)
 def bootstrap_admin(db, email, password)
```

---

## `app/services/agent.py`

> 有界 Agent：模型提出调用 → 参数验证 → 工具结果回填 → 继续或结束。

**imports**

```
import asyncio
import json
from time import perf_counter
from app.services.tools import TOOL_SCHEMAS, validate_call, execute_local
from app.services.agent_graph import run_graph
```

**symbols**

```
 async def run_agent(db, runtime, owner_id, data, token)
```

---

## `app/services/agent_graph.py`

> 将手写循环等价表达为 State / Node / Conditional Edge，复用同一执行器。

**imports**

```
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
```

**symbols**

```
class AgentState(TypedDict):
 async def run_graph(initial, decide, execute, max_iterations)
```

---

## `app/services/chat.py`

> 聊天状态与引用校验。状态写入独立 Session，客户端断流也不冒充成功。

**imports**

```
import re
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.platform import Conversation, Message
from app.services.knowledge import search
```

**symbols**

```
 def conversation_for(db, owner_id, identifier)
 async def prepare(db, runtime, owner_id, data)
 def validate_citations(answer, sources)
 def save_answer(bind, message_id, answer, status, citations, metrics)
```

---

## `app/services/device_service.py`

> Day 21：service 显式接收 Session；每个写操作拥有一个事务。

**imports**

```
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
```

**symbols**

```
 def calculate_total(prices)
 def group_devices(devices)
 def filter_alarm_devices(devices, level)
 def list_devices(db)
 def get_device(device_id, db)
 def create_device(data, db)
 def update_device(device_id, data, db)
 def delete_device(device_id, db)
```

---

## `app/services/knowledge.py`

> 上传→解析→切块→向量写入；SQL 保存状态，失败文档不会参与回答。

**imports**

```
import asyncio
import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from pypdf import PdfReader
from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session
from app.models.platform import Chunk, Document
from app.services.retrieval import bm25, rrf
```

**symbols**

```
 def parse_document(filename, content, max_chars)
 def split_text(text, size, overlap)
 def owned_document(db, identifier, owner_id)
 def document_path(runtime, document)
 async def upload(db, runtime, owner_id, filename, content, product, version)
 async def index_pages(db, runtime, document, pages)
 async def search(db, runtime, owner_id, query, top_k, product, version)
```

---

## `app/services/llm.py`

> 兼容 API 与演示模型共用接口；业务层不依赖某一家厂商 SDK。

**imports**

```
import asyncio
import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import AsyncIterator
import httpx
from app.core.settings import Settings
```

**symbols**

```
class ProviderError(Exception):
 def tokens(text)
class LLMProvider():
   def __init__(self, settings)
   async def close(self)
   def headers(self, key)
   async def post(self, url, body, key)
   async def complete(self, messages, tools)
   async def stream(self, messages)
   def demo_response(self, messages, tools)
   async def embed(self, texts)
```

---

## `app/services/mcp_client.py`

> MCP adapter：凭据仅传给本次受控子进程，不放在工具参数或模型消息中。

**imports**

```
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.core.settings import BACKEND_DIR
```

**symbols**

```
 async def execute_mcp(name, arguments, token, api_url)
```

---

## `app/services/retrieval.py`

> BM25 → RRF 融合 → 可选 CrossEncoder；每一步独立，方便替换。

**imports**

```
import math
from collections import Counter
from threading import Lock
from app.services.llm import tokens
```

**symbols**

```
 def bm25(query, texts)
 def rrf(rankings)
class Reranker():
   def __init__(self, model)
   def rank(self, query, candidates)
```

---

## `app/services/runtime.py`

> 应用生命周期资源：只创建一次模型 HTTP 客户端、向量库与限流器。

**imports**

```
import hashlib
import time
from collections import deque
from threading import Lock
from fastapi import HTTPException
from redis import Redis
from app.core.settings import Settings
from app.services.llm import LLMProvider
from app.services.vector_store import VectorStore
from app.services.retrieval import Reranker
```

**symbols**

```
class LoginLimiter():
   def __init__(self, url)
   def check(self, address)
class Runtime():
   def __init__(self, settings)
   async def close(self)
```

---

## `app/services/tools.py`

> Agent 的工具白名单。无 eval、任意 SQL、Shell 或真实设备写操作。

**imports**

```
import json
from fastapi import HTTPException
from sqlalchemy import select
from app.models import Device, Alarm
from app.schemas.platform import DeviceToolInput, AlarmToolInput, ManualToolInput
from app.services.knowledge import search
```

**symbols**

```
TOOL_MODELS = ...
TOOL_DESCRIPTIONS = ...
TOOL_SCHEMAS = ...
 def validate_call(name, arguments, device_id)
 async def execute_local(name, arguments, db, runtime, owner_id)
```

---

## `app/services/vector_store.py`

> Qdrant 本地与服务器模式；权限过滤必须在检索时执行。

**imports**

```
import hashlib
from threading import RLock
from qdrant_client import QdrantClient, models
from app.core.settings import Settings
```

**symbols**

```
class VectorStore():
   def __init__(self, settings)
   def upsert(self, chunks, vectors, owner_id, document)
   def search(self, vector, owner_id, product, version, limit)
   def delete(self, document_id)
   def close(self)
```

---

## `app/utils/__init__.py`

> 真正通用的小工具。

_(无顶层类/函数)_

---

## `exercises/__init__.py`

> 可独立运行的逐日实验，不自动修改业务数据库。

_(无顶层类/函数)_

---

## `exercises/day019_orm.py`

> uv run python -m exercises.day019_orm：临时库演示 ORM、JOIN 与事务。

**imports**

```
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.logging_config import logger
from app.database import build_engine, init_db
from app.models import Alarm, Device, User
```

**symbols**

```
 def run_demo(url)
```

---

## `scripts/benchmark.py`

> 测量 Atlas SSE；token 数必须来自模型服务，不能用字符数代替。

**imports**

```
import argparse
import getpass
import json
from time import perf_counter
import httpx
```

**symbols**

```
 def measure(client, headers, question)
 def main()
```

---

## `tests/conftest.py`

> 所有测试都使用临时 SQL 库、内存向量库和固定演示模型。

**imports**

```
import os
from tempfile import TemporaryDirectory
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from app.database import build_engine, get_db, init_db
from app.core.security import create_token, password_hasher
from app.models.platform import Account
import app.main
```

**symbols**

```
_data = ...
@fixture def db_engine(tmp_path)
@fixture def headers()
@fixture def viewer_headers()
@fixture def client(db_engine, monkeypatch)
```

---

## `tests/test_chat_failures.py`

**imports**

```
from app.services.llm import ProviderError
```

**symbols**

```
 def test_failed_stream_saved_and_can_continue(client, headers, monkeypatch)
 def test_login_rate_limit(client)
```

---

## `tests/test_device_api.py`

> 使用临时文件数据库；不连接或清空用户 app.db。

**imports**

```
import os
import subprocess
import sys
from pathlib import Path
import pytest
from sqlalchemy import select, func, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models import Alarm, Device
from app.schemas.device import DeviceCreate
from app.services import device_service
```

**symbols**

```
BODY = ...
 def test_crud_and_persistence(client, db_engine, headers)
 def test_guards_and_validation(client, headers)
 def test_failed_write_rolls_back_entire_transaction(db_engine)
 def test_restarted_process_reads_same_database(tmp_path)
```

---

## `tests/test_mcp_transport.py`

> 真实 stdio MCP 子进程测试；HTTP stub 验证令牌和三种返回类型。

**imports**

```
import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from app.services.mcp_client import execute_mcp
```

**symbols**

```
 def test_mcp_process_forwards_authenticated_http(monkeypatch)
```

---

## `tests/test_platform.py`

**imports**

```
import json
import asyncio
import httpx
import pytest
from app.services.knowledge import split_text, parse_document
from app.services.retrieval import bm25, rrf
from app.services.chat import validate_citations
from app.services.llm import ProviderError
from app.services.tools import validate_call
```

**symbols**

```
 def upload(client, headers, text)
 def test_auth_and_roles(client, headers, viewer_headers)
 def test_knowledge_citations_isolation_and_delete(client, headers, viewer_headers)
 def test_stream_and_empty_knowledge(client, headers)
@<decorator> def test_agent_calls_three_tools(client, headers, engine)
 def test_index_failure_not_searchable(client, headers, monkeypatch)
 def test_invalid_input_and_helpers(client, headers)
 def test_compatible_provider_contract(client, monkeypatch)
```

---

## `tests/test_provider_stream.py`

**imports**

```
import asyncio
import httpx
import pytest
from app.core.settings import Settings
from app.services.llm import LLMProvider, ProviderError
```

**symbols**

```
 def test_compatible_sse_content_and_usage()
 def test_truncated_sse_is_failure()
```

---

## `tests/test_schemas.py`

**imports**

```
import pytest
from pydantic import ValidationError
from app.schemas.device import DeviceCreate, DeviceUpdate
```

**symbols**

```
@<decorator> def test_blank_name_rejected(model)
 def test_name_normalized()
```

---

