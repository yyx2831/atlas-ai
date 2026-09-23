# 目录与职责

```text
atlas-ai/
├── README.md                     启动入口
├── backend/
│   ├── app/main.py               唯一 FastAPI 实例与生命周期
│   ├── app/cli.py                管理员初始化、虚构示例数据
│   ├── app/mcp_server.py         stdio MCP → 已认证 HTTP API
│   ├── app/core/                 配置、密码/JWT、日志
│   ├── app/database.py           engine、Session、建表
│   ├── app/dependencies.py       当前账户、管理员权限、Session 注入
│   ├── app/models/               原设备/教学用户/告警 + platform 新业务表
│   ├── app/schemas/              Pydantic 请求模型
│   ├── app/api/routes/           system/auth/devices/alarms/chat/knowledge/agent/protected
│   ├── app/services/             业务流程与外部模型/向量/MCP adapter
│   ├── tests/                    临时数据库和模拟 provider 集成测试
│   ├── scripts/benchmark.py      首文本延时与吞吐测量
│   ├── exercises/               原数据库专项练习
│   ├── .env.example              本地配置样例
│   └── Dockerfile                单 worker Python 镜像
├── frontend/
│   ├── src/App.vue               布局、页签、登录态
│   ├── src/components/           Login/Chat/Knowledge/Device/Agent/Settings
│   ├── src/stores/auth.ts         Pinia 账户状态
│   ├── src/api.ts                统一 HTTP、SSE、原文下载
│   ├── src/types.ts              前后端协议类型
│   ├── src/style.css             响应式样式
│   ├── vite.config.ts            开发代理 /api 去前缀
│   ├── nginx.conf                部署代理 /api 去前缀与 SSE
│   └── Dockerfile                Vue 构建 + Nginx
├── deployment/                  基础 Compose + Ollama/vLLM 覆盖文件
└── docs/                        45 天导读、模块文档、180 天历史补课
```

`backend/.data`、`.env`、node_modules、dist 不提交。默认数据库 `backend/app.db`；根目录旧 app.db 不再默认读取。历史已跟踪数据库仍保留，不自动删除。

Agent/MCP 深入教程位于 `docs/guides/agent-mcp/`：README 导航、完整教程、逐日章节和 `labs/` 可运行实验。示例使用独立虚构数据，Day 24 可显式连接 Atlas。
