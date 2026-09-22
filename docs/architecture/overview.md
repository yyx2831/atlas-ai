# 分层与数据流

前端只和 `/api` 通信。Vite/Nginx 去掉前缀，FastAPI 从 JWT 解析 Account，服务层显式接收 Session 和 Runtime。SQL 保存权威文档状态、消息与审计；Qdrant 保存可重建索引，磁盘保存原始文件。

上传：校验 → 保存原文/Document → 分块 → embedding → Qdrant → Chunk/ready；失败标记 failed，不进入搜索。
问答：账户校验 → 保存 pending 消息 → 混合检索 → 模型 → SSE → 校验引用 → 保存 completed/failed/cancelled。
Agent：模型选择工具 → 白名单与设备范围校验 → 本地函数或 MCP → 结构化结果 → 模型下一轮；图执行器复用相同节点函数。

外部失败不会静默变成演示结果。演示模式必须显式配置，页面显示标记。数据库会话不跨请求共享；Runtime 连接池在 lifespan 创建并关闭。部署只用单 worker，启动会修复残留 pending 消息和 running 任务。
