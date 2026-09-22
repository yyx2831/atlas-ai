# 服务层导航

accounts：账户创建；device_service：设备持久化；runtime：共享连接生命周期/登录限流；llm：模型协议；knowledge：文档与检索编排；vector_store：Qdrant；retrieval：BM25/RRF/重排；chat：会话与引用；agent/agent_graph：执行器；tools：工具契约；mcp_client：MCP 适配。业务函数接受显式依赖，不依赖 HTTP 请求的隐式全局状态。
