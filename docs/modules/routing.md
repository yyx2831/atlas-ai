# HTTP 路由

后端不带 `/api`；前端代理才使用该前缀。完整输入/输出见运行中 `/docs`。

- GET `/health`、`/ready`：公开健康探针。
- POST `/auth/login`；GET `/auth/me`；管理员 GET/POST `/auth/users`。
- `/devices` GET/POST，`/devices/{id}` GET/PUT/DELETE；读需要登录，写需要管理员。
- `/devices/{id}/alarms` GET/POST；写需要管理员。
- `/conversations` GET，`/conversations/{id}` GET/DELETE：仅本人。
- POST `/chat`、`/chat/stream`：普通 JSON 与 SSE。
- `/knowledge/documents` GET/POST，`/{id}` GET/DELETE，`/{id}/file` GET，`/{id}/reindex` POST。
- GET `/knowledge/search`：q、top_k、product、version；仅本人资料。
- `/agent/runs` POST/GET：运行与本人最近记录。
- GET `/system/info`：模式信息；`/me`、`/me/admin`、`/me/ping-db`：保留依赖注入练习。

旧 users.py、demo.py 源文件保留供教学，但 `/users`、`/external/test`、日志演示接口没有挂载到正式应用。
