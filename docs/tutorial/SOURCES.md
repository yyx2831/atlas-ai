# 官方资料与版本边界

资料核查日期：2026-09-19。教程不将 `latest` 当作永久不变的接口契约；实际实验应记录 lock 文件、SDK、镜像、模型 revision。

这次在线重点核查了 SQLAlchemy 2.0 select/scalars 与 Session 回滚（通过 context7 获取官方片段）、Pydantic 字段校验、Compose 启动顺序、LangGraph interrupt、MCP 当前规范入口和 vLLM 安全页面。下面其他链接作为官方学习入口，并不表示所有课程代码都已在你的硬件上运行过。

<a id="month-1"></a>
## 第一月

- [Python 官方教程](https://docs.python.org/3/tutorial/)：控制流、容器、模块与异常。
- [uv 项目管理](https://docs.astral.sh/uv/guides/projects/)：sync、run 与锁文件。
- [FastAPI 教程](https://fastapi.tiangolo.com/tutorial/)：路由、参数、Depends 与响应。
- [Pydantic 字段校验](https://docs.pydantic.dev/latest/concepts/validators/)：装饰器方法应在模型内注册。
- [SQLAlchemy 2.0 查询](https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html) 与 [Session FAQ](https://docs.sqlalchemy.org/en/20/faq/sessions.html)：教程采用 select/scalars，失败后显式 rollback。
- [Alembic 教程](https://alembic.sqlalchemy.org/en/latest/tutorial.html)：环境、revision 与升级流程。
- [PostgreSQL 教程](https://www.postgresql.org/docs/current/tutorial.html) 与 [EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)：SQL 与执行计划。
- [Microsoft WSL](https://learn.microsoft.com/windows/wsl/)：Windows/Linux 环境边界。

<a id="month-2"></a>
## 第二月

- [Docker 构建](https://docs.docker.com/build/) 与 [Compose 启动顺序](https://docs.docker.com/compose/how-tos/startup-order/)：就绪检查与启动依赖。应用仍要处理运行中的连接失败。
- [Nginx proxy 模块](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)：URI 替换、缓冲和超时。
- [MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)：事件帧格式。
- [Qdrant 文档](https://qdrant.tech/documentation/)：collection、payload、过滤与快照。
- [HTTPX 文档](https://www.python-httpx.org/)：异步客户端、超时与流。
- [Vue 官方指南](https://vuejs.org/guide/introduction.html) 与 [Vite 构建](https://vite.dev/guide/build.html)：前端沿用已有经验，不重复安排基础课程。

<a id="month-3"></a>
## 第三月

- [LangGraph 概览](https://docs.langchain.com/oss/python/langgraph/overview) 与 [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)：暂停需要 checkpointer 与 thread_id，恢复会重新进入节点，因此副作用应幂等且放在批准之后。
- [MCP 规范入口](https://modelcontextprotocol.io/specification/latest)：核查时跳转到 2026-07-28，介绍 stateless 核心；这不表示你的 SDK 已支持全部新能力。
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)：采用所安装版本的示例与兼容说明。教程 stdio 示例用来验证最小工具调用，不自行声称实现全部最新规范。
- [Qdrant 混合查询](https://qdrant.tech/documentation/concepts/hybrid-queries/)：服务端能力需核对部署版本。教程 RRF 为可独立理解的教学实现。

<a id="month-4"></a>
## 第四月

- [vLLM 文档](https://docs.vllm.ai/en/latest/) 与 [安全说明](https://docs.vllm.ai/en/latest/usage/security/)：按实际版本核对兼容硬件、参数及端点保护范围。
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)：按发行版安装和验证。
- [CUDA 兼容说明](https://docs.nvidia.com/deploy/cuda-compatibility/)：驱动、runtime 与兼容边界。
- [Ollama 文档](https://docs.ollama.com/)：模型管理、本地 API 与能力限制。

<a id="month-5"></a>
## 第五月

- [Prometheus 指标类型](https://prometheus.io/docs/concepts/metric_types/) 与 [Python 客户端](https://prometheus.github.io/client_python/)：标签、Histogram 与多进程部署须分别核对。
- [Grafana 文档](https://grafana.com/docs/grafana/latest/)：数据源、查询与告警。
- [NVIDIA DCGM Exporter](https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/latest/dcgm-exporter.html)：GPU 遥测。
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html)：备份格式与版本要求。
- [pip download](https://pip.pypa.io/en/stable/cli/pip_download/) 与 [uv export](https://docs.astral.sh/uv/reference/cli/#uv-export)：离线依赖准备。

<a id="month-6"></a>
## 第六月

- [pytest 文档](https://docs.pytest.org/en/stable/)：fixture、隔离与断言。
- [GitHub Actions](https://docs.github.com/en/actions)：若项目采用 GitLab，则改读其官方 CI 文档。
- [Kubernetes 概念](https://kubernetes.io/docs/concepts/) 与 [kind 快速开始](https://kind.sigs.k8s.io/docs/user/quick-start/)：本地基础实验，不等同生产集群运维资质。

招聘要求、模型价格和硬件采购信息应在实际决策时重新查询，课程不提供会过期的固定采购结论，也不虚构岗位样本或付费课程内容。
