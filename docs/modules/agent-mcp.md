# Agent 与 MCP

tools.py 定义三个工具的 JSON schema 与严格参数模型：get_device、get_alarm、search_manual。LLM 只能提出调用，后端验证工具名和参数；device_id 必须与当前用户选中的设备一致。工具不执行任意 SQL、shell 或设备写操作。

agent.py 手写循环：decide → execute → decide，最多 5 轮、每轮 3 次工具调用、每工具 25 秒、任务默认 90 秒。错误变成结构化 ok:false 回填给模型，步骤保存工具名/结果/耗时，不保存不可见思维过程。agent_graph.py 使用 StateGraph 的条件边重用相同逻辑。

本地模式直接调用 service；MCP 模式启动固定 python -m app.mcp_server，经 stdio initialize/list_tools/call_tool，服务通过 JWT 访问本应用 HTTP API。子进程命令和地址来自服务器配置，模型无法指定。令牌在环境传递，不放工具参数或模型上下文。每次工具调用创建短生命周期进程，便于理解，代价是较高延时。

修改监听端口时同步 MCP_API_URL。MCP 包固定在 1.x 以匹配 FastMCP 导入。若只看到了“已完成”仍需核对每一步 ok，任务完成不表示每个工具成功。故障假设不是已确认根因，登记信息不是实时遥测。

MCP 返回使用完整泛型标注与 structured_output，避免裸 list 被拆成多个文本块。回归测试实际启动 stdio 子进程，验证设备对象、告警数组和手册数组。内部 HTTP 明确 trust_env=False，防止本机代理截走请求。
