# 关键实验手册

这些是逐课配套的教学示例，不是一键安装整个 Atlas 的脚本。带占位符的配置需要填写实际测试值；代码片段只在说明的目录与环境运行。后续生产化仍要完成对应课程的权限、事务、超时和恢复任务。

<a id="day-001"></a>
## Day 1：看清环境

```powershell
Set-Location E:\Codes\atlas-ai\backend
uv sync --locked
uv run python -c "import sys; from pathlib import Path; print(sys.executable); print(Path.cwd())"
```

此处 print 仅用于一次性诊断脚本，业务 API 沿用项目 logger。不要复制原计划的 `uv init backend` 覆盖已有工程。

<a id="day-006"></a>
## Day 6：生效的字段校验

下面方法应位于模型类内部。对 `DeviceUpdate` 的可选 name 也要定义相应校验，允许 None 或拒绝 None 的策略需与接口一致。

```python
from pydantic import BaseModel, Field, field_validator

class NameInput(BaseModel):
    name: str = Field(min_length=1)

    @field_validator('name')
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('name 不能为空')
        return value

assert NameInput(name='  router  ').name == 'router'
```

独立练习：`NameInput(name='   ')` 必须抛 ValidationError。把这个方法迁移进现有 DeviceCreate，不能只把函数放在文件顶层。

<a id="day-009"></a>
## Day 9：Depends 的边界

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

# 路由参数由框架解析；普通业务函数显式传参。
def count_devices_service(db: Session) -> int:
    from sqlalchemy import select, func
    from app.models import Device
    return db.scalar(select(func.count()).select_from(Device)) or 0

def example_endpoint(db: Annotated[Session, Depends(get_db)]):
    return {'count': count_devices_service(db)}
```

这是未注册的示例函数，不会自动出现在 /docs。直接调用 example_endpoint 需要自己传 Session；依赖解析发生在 FastAPI 的请求处理中。

<a id="day-010"></a>
## Day 10：串行 await 与 gather

保存为独立练习文件，用 `uv run python 文件路径` 执行：

```python
import asyncio
from time import perf_counter

async def io_job(n: int) -> int:
    await asyncio.sleep(1)
    return n

async def main():
    start = perf_counter()
    serial = [await io_job(n) for n in range(3)]
    serial_seconds = perf_counter() - start
    start = perf_counter()
    parallel = await asyncio.gather(*(io_job(n) for n in range(3)))
    parallel_seconds = perf_counter() - start
    assert serial == parallel == [0, 1, 2]
    print({'serial_s': serial_seconds, 'parallel_s': parallel_seconds})

asyncio.run(main())
```

约 3 秒对 1 秒，差异来自独立 IO 等待重叠。不要把精确耗时写成脆弱断言。

<a id="day-032"></a>
## Day 32：教学 Dockerfile

`backend/Dockerfile` 示例；选择 Python 3.12 是课程基线，不表示它永远最新。镜像正式交付时固定 digest。

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY app ./app
COPY README.md ./README.md
RUN uv sync --locked --no-dev
RUN useradd --create-home atlas && chown -R atlas:atlas /app
USER atlas
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`.dockerignore` 至少包含：

```text
.venv
.git
.env
.env.*
*.db
__pycache__
```

如果项目 uv.lock 与所选 uv 不兼容，以该项目验证过的 uv 版本替换镜像 tag 并记录。Day 21 后需要传 DATABASE_URL 才能启动；未完成该课时当前 SQLite 仍属于容器内临时演示。

<a id="day-036"></a>
## Day 36：最小 Compose

保存为 `deployment/compose.yaml`。在 deployment 内创建不提交的 `.env.lab`，设置本地测试密码变量 ATLAS_DB_PASSWORD 和完整 DATABASE_URL。URL 用户/密码/库名必须与 postgres 配置一致，密码中的 URL 保留字符须编码。

```yaml
services:
  api:
    build: ../backend
    environment:
      DATABASE_URL: ${DATABASE_URL:?set DATABASE_URL}
    ports:
      - "127.0.0.1:8001:8000"
    depends_on:
      postgres:
        condition: service_healthy
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: atlas_lab
      POSTGRES_DB: atlas_api_lab
      POSTGRES_PASSWORD: ${ATLAS_DB_PASSWORD:?set ATLAS_DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U atlas_lab -d atlas_api_lab"]
      interval: 5s
      timeout: 3s
      retries: 10
  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  pgdata:
```

这是基础栈，没有自动迁移，也没有把 Redis 用在业务中。Day 37 再为 API 增加就绪探针。当前 Dockerfile 未复制 migrations；要在镜像中执行迁移，增加 `COPY alembic.ini ./` 与 `COPY migrations ./migrations` 后重新构建。

```bash
docker compose --env-file .env.lab up -d postgres redis
docker compose --env-file .env.lab run --rm api uv run alembic upgrade head
docker compose --env-file .env.lab up -d api
```

上面迁移命令依赖 Day 20 和镜像复制配置已经完成。若数据库密码之后变更，现有持久卷不会因为修改 POSTGRES_PASSWORD 自动改旧账户密码，需要明确执行密码轮换；不要删卷解决。

<a id="day-038"></a>
## Day 38：前缀与反代

以下放入测试 Nginx 的 server 配置。示例假定 Nginx 与 API 在同一宿主网络、API 在 8000；如果都在 Compose 内，则上游写 `http://api:8000/`。

```nginx
server {
    listen 80;
    server_name localhost;
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`/api/health` 变为上游 `/health`。去掉 proxy_pass 尾斜杠后行为不同，应做对照。配置改完先 `nginx -t` 再 reload；Swagger 的外部路径另作验证，不假设反代后文档页自动正确。

<a id="day-042"></a>
## Day 42：不依赖模型的 SSE

示例 router，注册到现有聚合路由，不新建 FastAPI app。

```python
import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get('/stream-lab')
async def stream_lab(request: Request):
    async def events():
        for n in range(5):
            if await request.is_disconnected():
                return
            yield f'data: {json.dumps({"n": n})}\n\n'
            await asyncio.sleep(0.3)
        yield 'event: done\ndata: {}\n\n'
    return StreamingResponse(events(), media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
```

用 `curl -N http://127.0.0.1:8000/stream-lab`，Windows 写 curl.exe。每约 0.3 秒看到一个事件。前端解析示例只针对这里的 `\n\n`、单行 data 协议；接通真实 provider 前应支持标准 SSE 的 CRLF、多行 data 和注释，或使用已验证解析库。

```javascript
const response = await fetch('/api/stream-lab');
if (!response.ok || !response.body) throw new Error('stream unavailable');
const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
let buffer = '';
while (true) {
  const {value, done} = await reader.read();
  if (done) break;
  buffer += value;
  let boundary;
  while ((boundary = buffer.indexOf('\n\n')) >= 0) {
    const frame = buffer.slice(0, boundary);
    buffer = buffer.slice(boundary + 2);
    const data = frame.split('\n').find(line => line.startsWith('data:'));
    if (data) console.log(JSON.parse(data.slice(5).trimStart()));
  }
}
```

业务版需要 AbortController、错误事件、结束事件和缓冲大小上限，前端日志仅作本实验观察。

<a id="day-047"></a>
## Day 47：余弦

```python
from math import sqrt, isclose

def cosine(a: list[float], b: list[float]) -> float:
    if not a or len(a) != len(b):
        raise ValueError('vectors must have the same nonzero dimension')
    na = sqrt(sum(x*x for x in a))
    nb = sqrt(sum(x*x for x in b))
    if na == 0 or nb == 0:
        raise ValueError('zero vector has no cosine similarity')
    return sum(x*y for x,y in zip(a,b)) / (na*nb)

assert isclose(cosine([1,0],[2,0]), 1)
assert isclose(cosine([1,0],[0,1]), 0)
assert isclose(cosine([1,0],[-1,0]), -1)
```

真实 embedding 还要拒绝 NaN/inf 并校验模型版本。本例只演示公式。

<a id="day-051"></a>
## Day 51：能证明终止的切块

```python
def chunk_text(text: str, size: int = 500, overlap: int = 80) -> list[dict]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError('require size > overlap >= 0')
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append({'start': start, 'end': end, 'text': text[start:end]})
        if end == len(text):
            break
        start = end - overlap
    return chunks

assert chunk_text('') == []
assert [x['text'] for x in chunk_text('abcdef',4,1)] == ['abcd','def']
```

步长 `size-overlap` 必须为正；生产还需要标题、句段、token 预算与页码映射。

<a id="day-062"></a>
## Day 62：按名次融合

```python
def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    if k <= 0:
        raise ValueError('k must be positive')
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen = set()
        for rank, chunk_id in enumerate(ranking, 1):
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1/(k+rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))

assert rrf([['A','B'],['B','C']])[0][0] == 'B'
```

常量 60 是教学起点，不保证你的数据最优。每路候选先规范化去重，结果排序固定便于复现。

<a id="day-066"></a>
## Day 66：指标手算对照

```python
def retrieval_metrics(retrieved: list[str], relevant: set[str], k: int):
    if k <= 0:
        raise ValueError('k must be positive')
    if not relevant:
        return None  # 单独评估无答案题
    found = set(retrieved[:k]) & relevant
    return {'hit': int(bool(found)), 'recall': len(found)/len(relevant)}

assert retrieval_metrics(['A','C'], {'A','B'}, 2) == {'hit': 1, 'recall': 0.5}
```

宏平均只在符合定义的有标注可回答题上计算；无答案题另看错误回答率。先去重候选能避免重复块浪费 K，但重复结果不能重复算命中。

<a id="day-072"></a>
## Day 72：最小白名单执行器

独立 mock，展示验证顺序。实际权限应查可信身份和对象范围，不让模型传入 role。

```python
from pydantic import BaseModel, ConfigDict, Field

class DeviceArgs(BaseModel):
    model_config = ConfigDict(extra='forbid')
    device_id: int = Field(gt=0, strict=True)

def execute(name: str, arguments: dict, permissions: set[str]) -> dict:
    if name != 'get_device':
        raise ValueError('unknown tool')
    args = DeviceArgs.model_validate(arguments)
    if 'read_device' not in permissions:
        raise PermissionError('forbidden')
    # 实际实现还必须验证 args.device_id 所属租户。
    return {'id': args.device_id, 'status': 'mock-online'}

assert execute('get_device', {'device_id': 1}, {'read_device'})['id'] == 1
```

权限在服务器执行上下文注入。接真实工具时添加 deadline、结果上限、审计和幂等，不能把这段 mock 当完整安全实现。

<a id="day-076"></a>
## Day 76：循环契约参考

下面是**接口伪代码**，`provider.next` 和 `executor.run` 需要实现，不可直接执行。关键是 assistant 工具提案与每个 call_id 的结果都进入历史。

```text
messages = 本次独立任务的初始消息
deadline = 现在 + 总预算
for iteration in range(5):
    response = provider.next(messages, tools, deadline)
    messages.append(response.assistant_message)
    if response has no tool_calls:
        return response.final_answer
    for call in response.tool_calls:
        result = executor.run(call.name, call.arguments, trusted_context, deadline)
        messages.append(tool_result_message(call.id, result))
return explicit_limit_reached_result
```

测试 provider 固定返回“工具→最终回答”，再固定返回五次工具循环。后者必须停止。工具调用数也要独立限额，因为一轮可能含多个调用。

<a id="day-082"></a>
## Day 82：暂停要放在副作用之前

下面仅为 LangGraph 节点片段，需在 Day 79 的图中编译 checkpointer，并提供稳定 thread_id。内存 checkpointer 仅演示，跨进程必须持久化。

```python
from langgraph.types import interrupt

def approval_node(state):
    decision = interrupt({
        'action': 'restart_device_mock',
        'device_id': state['device_id'],
        'approval_id': state['approval_id'],
    })
    # 真实实现必须由后端验证审批者权限、绑定参数、过期和幂等。
    return {'approved': decision is True}
```

下一节点先校验服务器批准记录，再写一条模拟操作审计。恢复使用同一 thread_id 和 `Command(resume=True)`；这个布尔值本身不构成安全授权。重新进入节点时 interrupt 之前的代码可能再次执行，所以那里不能放设备重启。

<a id="day-085"></a>
## Day 85：stdio MCP 最小往返

在独立 `labs/device-mcp` uv 工程安装官方 `mcp` 包并锁定版本；如果安装版本调整了导入或方法，按 SOURCES 的 SDK 文档同步。不要误用同名非官方包。

`server.py`：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('atlas-device-lab')

@mcp.tool()
def get_device(device_id: int) -> dict:
    if device_id != 1:
        return {'ok': False, 'error': 'not_found'}
    return {'ok': True, 'device': {'id': 1, 'name': 'mock-router'}}

if __name__ == '__main__':
    mcp.run(transport='stdio')
```

同目录 `client.py`：

```python
import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable,
        args=[str(Path(__file__).with_name('server.py'))])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert any(t.name == 'get_device' for t in tools.tools)
            result = await session.call_tool('get_device', {'device_id': 1})
            print(result)

asyncio.run(main())
```

执行 `uv run python client.py`，client 的 print 可用于观察；server stdout 留给协议。此处为 SDK 的 stdio 入门模式，不代表所有传输或所有 2026 规范扩展均已验证。

<a id="day-093"></a>
## Day 93：权重下界

```python
def weight_size(parameters: int, bits: int):
    nbytes = parameters * bits / 8
    return {'GB': nbytes / 10**9, 'GiB': nbytes / 2**30}

assert weight_size(32_000_000_000, 16)['GB'] == 64
assert weight_size(32_000_000_000, 4)['GB'] == 16
```

不是完整显存估算，尚未加入 KV cache、激活、运行时、量化尺度与安全余量。

<a id="day-122"></a>
## Day 122：有界标签

安装并锁定 prometheus-client 后可在独立练习验证：

```python
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

registry = CollectorRegistry()
requests = Counter('atlas_requests_total', 'Completed requests',
    ['method','route','status_class'], registry=registry)
latency = Histogram('atlas_request_duration_seconds', 'Request duration',
    ['route'], registry=registry, buckets=(0.01,0.05,0.1,0.5,1,5,10))
requests.labels('GET','/devices/{id}','2xx').inc()
latency.labels('/devices/{id}').observe(0.04)
assert b'atlas_requests_total' in generate_latest(registry)
```

在实际中间件对成功和异常都记录；路由模板在匹配后取得，未匹配路由使用固定 unknown，不能回退到任意 URL 标签。

<a id="day-148"></a>
## Day 148：与目标一致的 wheelhouse

在和目标相同 Linux/架构/Python 的在线准备环境执行，`work-offline` 为新建临时目录：

```bash
uv export --locked --no-dev --no-emit-project -o requirements-offline.txt
python3 -m venv work-offline
work-offline/bin/python -m pip download --only-binary=:all: \
  -r requirements-offline.txt -d wheelhouse
```

若没有匹配 wheel，应在匹配环境构建并保存构建依赖，不通过移除全部限制假装已离线就绪。离线新环境：

```bash
python3 -m venv offline-check
offline-check/bin/python -m pip install --no-index --find-links=wheelhouse \
  -r requirements-offline.txt
offline-check/bin/python -c "import fastapi, sqlalchemy, httpx"
```

此流程故意使用 pip 验证 wheelhouse，不替换项目 uv 主流程。应用源码可从 backend 工作目录直接运行；若要 `pip install` 项目自身，还需预先构建项目 wheel 和完整构建依赖，不要在离线机触发隐式联网构建。

<a id="day-177"></a>
## Day 177：无数据库的 K8s 健康实验

先创建独立 lab API，避免把当前需要 DATABASE_URL 的业务镜像直接部署：

```python
# 独立 labs/k8s/main.py；不是 backend/app/main.py
from fastapi import FastAPI
app = FastAPI()
@app.get('/health')
def health():
    return {'status': 'ok'}
```

为这个独立应用建镜像，依赖选择项目已验证的固定 FastAPI/uvicorn 版本，标记 `atlas-health:lab`，容器监听 0.0.0.0:8000。创建 kind 后导入镜像：

```bash
kind create cluster --name atlas-lab
kind load docker-image atlas-health:lab --name atlas-lab
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: atlas-health
spec:
  replicas: 1
  selector:
    matchLabels: {app: atlas-health}
  template:
    metadata:
      labels: {app: atlas-health}
    spec:
      containers:
        - name: api
          image: atlas-health:lab
          imagePullPolicy: IfNotPresent
          ports: [{containerPort: 8000}]
          readinessProbe:
            httpGet: {path: /health, port: 8000}
---
apiVersion: v1
kind: Service
metadata:
  name: atlas-health
spec:
  selector: {app: atlas-health}
  ports: [{port: 8000, targetPort: 8000}]
```

保存后在专用 kind 上 `kubectl --context kind-atlas-lab apply -f lab.yaml`，再 `kubectl --context kind-atlas-lab port-forward service/atlas-health 8001:8000`，访问本机 8001/health。显式 context 防止误改其他集群。

<a id="day-180"></a>
## Day 180：评分与必过项

总分 100：需求与假设 10，后端与数据 15，RAG 与引用 20，Agent/MCP 15，权限与审批 15，部署离线与恢复 15，可观测与排障 10。每项必须附真实证据；未实测不计已通过。80 分可作为个人阶段目标，不构成职业认证。

无论总分多少，以下任一失败均需先补课：跨租户读取、未批准执行写动作、伪造引用、秘密泄露、备份无法恢复。真实设备控制未接入时只验收模拟执行器，不宣称完成生产设备安全认证。

最终交付目录建议：需求、架构、安装包清单、部署说明、验收结果、性能原始记录、运维手册、故障手册、备份恢复报告、已知限制。演示“设备 X 断连”时依次展示事实、告警、手册依据、诊断假设和审批，明确哪一步是推断。
