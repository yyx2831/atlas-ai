# 如何安全地改代码

## 先理解一条请求

打开 main.py 看 include_router，再跟到 devices.py → schemas/device.py → services/device_service.py → models/device.py → database.py。路由处理 HTTP，Pydantic 检查输入，service 执行业务，ORM 描述表。不要把所有逻辑塞回 main.py。

## 常见修改位置

- 改模型、超时、chunk：先改 backend/.env，参数声明看 core/settings.py。settings 被缓存，修改后重启。
- 增加设备字段：ORM → 输入/输出 schema → service → frontend/types.ts 与 DeviceView.vue；已有表必须迁移，再测创建、修改、重启读取。
- 增加工具：tools.py schema/验证/执行 → mcp_server.py 同名工具 → Agent 测试；不要让模型任意调用 Python 函数。
- 调整检索：先用 /knowledge/search 看真实候选，再调 retrieval.py，最后检查引用。回答好看不等于检索正确。
- 改页面：components/ 对应页面，通用请求放 api.ts，登录态放 Pinia。API 字段改变时同步 types.ts。

## 本地数据与常见问题

先停止后端，再运行带 --demo 的 CLI；本地 Qdrant 同一目录不能被两个进程同时打开。初始化已有账户不会重置密码。忘记密码应通过明确的管理脚本重置哈希，不要把数据库删掉。

401：重新登录，确认初始化的数据库和运行时一致。403：成员没有管理员写权限。422：读 detail 字段检查参数。502：查模型地址、key、模型名和日志。知识库空：检查 owner、产品版本、状态和 index_key；改 embedding 后重建。端口占用：换 Vite 端口；后端改端口要同步 Vite ATLAS_DEV_API 与 MCP_API_URL。

## 验证和修改节奏

每次只改变一个行为，用现有测试复现预期，再改实现。backend 的 pytest 使用临时数据库，不访问你的 app.db；frontend 测试覆盖 SSE 解析与登录错误。运行 README 中测试命令，最后 python _gen_repomap.py 更新源码地图。禁止提交 .env、模型 key、生成数据或 node_modules。

本轮没有自动改写原数据库，也没有执行生产设备命令。当前交付是可运行的学习应用；生产化需要补数据库迁移、备份演练、任务队列、可观测性和业务级质量评估，应按真实负载逐项完成。
