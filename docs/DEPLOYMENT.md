# Docker / Linux 部署与排障

## 先启动演示模型的整套服务

要求 Docker Engine/Desktop 与 Compose 可用。命令在 `deployment` 目录执行。

```powershell
cd E:\Codes\atlas-ai\deployment
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(24)); print(secrets.token_hex(32))"
```

把第一行填入 `POSTGRES_PASSWORD`，第二行填入 `JWT_SECRET`，自己填写 `ADMIN_EMAIL` 和至少 12 字符的 `ADMIN_PASSWORD`。不要提交 `.env`。这里数据库密码用 hex，避免数据库 URL 中的 `@`、`/` 等字符需要额外编码。已有账户不会被环境变量重置密码。

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail 100 backend
```

访问 http://127.0.0.1:8080 。Compose 自动创建初始管理员；在页面添加设备、告警并上传你自己的手册，或使用 `docs/samples/router-manual.md`。无需运行 CLI。数据库、Redis、Qdrant、原始文件分别持久化到 volume；它们不向宿主机暴露端口。

停止但保留数据：`docker compose down`。**不要添加 `-v`，它会删除这些数据卷。** 首次配置 PostgreSQL 后，改 `.env` 不会改掉已有数据库用户密码；应在数据库内执行密码变更后同步连接配置。

## 请求路径与流式返回

浏览器请求 `/api/chat/stream` → Nginx 去掉 `/api` → FastAPI `/chat/stream`。Nginx 禁用代理缓冲并延长超时。前端不存模型 API Key，只存当前会话的短期 JWT。Swagger 经代理访问时可直接读 schema `/api/openapi.json`；交互调试推荐本地开发后端的 `/docs`（其默认 OpenAPI URL 是根路径）。

默认只绑定 `127.0.0.1:8080`。Linux 远程演示可通过 SSH 转发：`ssh -L 8080:127.0.0.1:8080 user@server`。正式公网入口需部署域名/TLS 反向代理，再决定监听地址、防火墙和账户策略。当前 Compose 是单机基线，不包含自动扩缩容。

## 健康检查与启动顺序

PostgreSQL/Redis 健康后启动后端；Qdrant 创建 collection 失败会使后端启动失败，restart 会重试；后端 `/ready` 检查数据库、Qdrant 和配置后的 Redis，健康后启动 Web。`/health` 只证明 Web 进程响应。依赖故障恢复后再看 `/ready`，不要只看页面静态资源。

保留 `--workers 1`。文档索引锁和会话并发检查属于单进程设计；多副本需改为任务队列、数据库锁/唯一约束、集中任务恢复。Redis 当前用于登录限流，不是假装存在的缓存/队列。

## 备份与恢复

至少一起备份 PostgreSQL（`pg_dump`）、`app-data` 原文与 `qdrant-data`，保持同一时间窗口。Redis 登录计数可重建。学习环境最简单的做法是停写后备份卷；恢复后核对文档列表、原文下载与引用，再开放写入。不要把 Windows 默认 SQLite 文件直接挂作 PostgreSQL 数据目录。需要迁移旧设备时应写显式导出/导入脚本并先备份。

## 排障顺序

1. 进程：`docker compose ps`，确认服务没有重启循环。
2. 端口：Linux `ss -lntp`；Windows `Get-NetTCPConnection -LocalPort 8080`。冲突时改 `WEB_PORT`。
3. 网络：`docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://qdrant:6333/readyz').status)"`。
4. 日志：`docker compose logs --tail 100 backend web postgres`，按 request_id 对照一次请求。
5. 配置：核对服务名称和端口。容器里的 localhost 是容器自身，不能用它指宿主机 Ollama。

故障练习：停止 backend 观察 502，重启后复测；停止 postgres 观察 `/ready` 失败；把 WEB_PORT 改成已占端口观察启动报错，再恢复。只在自己的练习环境操作。

CPU 演示无需 GPU。真实模型配置见 [本地模型](LOCAL-MODELS.md)。当前交付只完成配置静态校验，未在本机运行完整 Docker 栈。
