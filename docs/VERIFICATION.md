# 本轮验证记录 · 2026-09-22

- 后端：20 项 pytest 通过；包含真实 MCP stdio 子进程 → 本地 HTTP stub 的协议测试，及权限、文档隔离、引用、SSE 错误恢复、两种 Agent 执行器与设备重启持久化。
- 前端：3 项 Vitest 通过；vue-tsc 类型检查与 Vite 生产构建通过；Ruff F 规则检查通过。
- 浏览器：Headless Chromium 实测登录、上传、RAG 流式问答、引用弹窗、认证原文下载、刷新后的历史、loop/local、loop/MCP、graph/MCP；三步工具均返回成功，未出现页面 JS 错误。
- 390px 宽度检查无横向溢出。真实截图在 docs/assets/workspace.png 与 agent.png。
- Docker Compose 基础文件、Ollama/vLLM 合并配置通过 config --quiet。未启动完整 Docker 栈，未做 PostgreSQL/Redis/Qdrant server 联调，未验证真实云模型、reranker 或 GPU 推理。功能演示与真实质量验证分开记录。

浏览器服务使用独立临时数据库与示例账号，没有写入原 backend/app.db。原根目录 app.db 保留。测试脚本中没有生产密钥。本轮未提交 Git。

下一次真实环境验收：从新管理员账户登录 → 创建 Router-A/告警 → 上传手册 → 实际模型聊天 → 重建真实向量索引 → 核对引用 → MCP 分析 → 重启服务确认持久化。记录模型/镜像版本与硬件，并运行 benchmark。
