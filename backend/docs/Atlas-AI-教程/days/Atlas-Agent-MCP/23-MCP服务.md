# Day 23：写一个独立的 device-mcp-server

前六天，工具函数和 Agent 在一个 Python 进程里。今天把工具放到另一个进程，让客户端通过 MCP 找到并调用它。先使用虚构数据，把协议问题和数据库问题分开。

## 1. 什么时候需要 MCP

如果一个工具永远只给这一个应用使用，直接调用 Python service 很清楚。若希望相同工具服务被不同 AI 应用接入，大家需要一套共同的名称、参数、发现和调用约定。

MCP 做这层协议约定。它本身不决定模型选什么工具，也不自动产生业务权限。应用仍要把可用工具整理给模型，并处理模型的返回。

在本实验中：

- Host 是运行学习脚本的应用；Atlas 集成里则是 Atlas。
- Client 是 `ClientSession`，负责与服务连接和交互。
- Server 是 `device_server.py` 子进程，实际提供三个工具。

进程隔离不等于换了一台机器。stdio 可以在同一台电脑上让父子进程通信；远程服务还可以选择 HTTP 类传输。本教程只实现项目实际使用的 stdio，不额外引入远程 MCP 鉴权流程。

## 2. 当前版本的通信顺序

```text
启动子进程
  → initialize：协商版本与能力
  → list_tools：服务有哪些工具，输入是什么
  → call_tool：调用某个工具
  → 读取结构化结果或错误
  → 关闭会话与子进程通道
```

这些方法由项目 MCP 1.x SDK 提供。对应这一代协议，初始化先于正常工具操作；不是一启动就随便往 stdin 写一个业务 JSON。[版本化生命周期规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)

官网当前最新协议页面可能使用不同发现流程。本教程保持项目已经安装并测试过的 SDK，用 lock 文件确定环境，不要求你为看教程先迁移协议。

## 3. 服务端：普通函数上加协议入口

核心代码来自配套 `labs/device_server.py`：

```python
from typing import Any
from mcp.server.fastmcp import FastMCP
import tools_lab

mcp = FastMCP("device-mcp-server-lab")

@mcp.tool(structured_output=True)
async def get_device(device_id: int) -> dict[str, Any]:
    args = tools_lab.DeviceInput(device_id=device_id)
    return tools_lab.get_device(args.device_id)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

FastMCP 负责把函数注册成工具，读取参数类型/文档说明并处理协议。内部调用的 get_device 仍是昨天那个普通函数。协议入口不应该重复实现所有业务逻辑。

`async def` 与 `mcp.tool` 不会自动添加你所有业务约束；设备存在、权限和范围仍要校验。实验使用虚构数据，正式服务则在 Day 24 访问已认证 API。

## 4. 为什么完整返回类型很重要

告警返回数组，写成：

```python
async def get_alarm(device_id: int, limit: int = 10) -> list[dict[str, Any]]:
    ...
```

结合 `structured_output=True`，让 SDK 构造稳定的结构化输出。当前项目曾遇到裸 list 返回被当成多个文本块的情况：一个告警看似能解析，多个告警拼起来却成了两段 JSON，`json.loads` 报 Extra data。

再一个真实错误：裸 `dict` 配合强制 structured_output 在这套 SDK 中不能正常生成所需输出模型。明确写 `dict[str, Any]`，并用多条记录测试，避免依赖偶然的单条结果。

这是当前 SDK/注解组合的行为经验，不应推导成“所有 MCP 实现都一定用同一个 Python 返回包装”。

## 5. 客户端的核心代码

```python
params = StdioServerParameters(
    command=sys.executable,
    args=[str(server_path)],
)
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        listing = await session.list_tools()
        result = await session.call_tool("get_device", {"device_id": 1})
```

`sys.executable` 指当前解释器，确保子进程也用安装了 MCP 的那套 Python。不要一边用 `.venv` 客户端，一边用系统 `python` 启动缺依赖的服务。

两个 `async with` 管资源生命周期：建立通道和会话，结束时释放。不是把子进程启动后遗忘在后台。

## 6. 读结果，别只看有没有文本

```python
if result.isError:
    raise ValueError("工具执行失败")
payload = result.structuredContent
value = payload.get("result", payload)
```

在本教程版本中，SDK 常用对象直接作为 structuredContent，而数组等形状可能包装成 `{"result": [...]}`。客户端解出业务值。这个 `result` 键是适配当前返回形状，不是对所有外部 MCP 服务器都通用的绝对假设。

MCP 工具结果可以同时有 content 文本块、structuredContent 结构化字段与 isError 状态；协议层错误和工具执行错误也有不同路径。先检查错误，再按已知工具契约解码。[版本化工具规范](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)

Atlas 的客户端有纯文本 JSON 回退，但这不是万能解析器：不能保证任意文本、图片、多个不相关 JSON 文本块都能变成你预期的业务数据。

## 7. 运行真实 stdio 实验

```powershell
& $Py "$Lesson\labs\mcp_lab.py"
```

不需要提前单独启动 device_server；客户端会启动它。预期依次看到三个工具名、设备对象、两条告警、手册数组，最后：`不存在的设备：isError=True（符合预期）`。

这次通信和子进程是真的，数据是虚构的，也没有 LLM 参与。能成功说明协议链路能跑，尚不能证明模型会正确选工具。

若手动运行 `python device_server.py` 之后终端似乎不动，多半是在等待 stdin 协议输入；它不是 HTTP 网页服务，不要用浏览器去猜一个端口。

## 8. stdout 为什么不能随便 print

stdio 的 stdout 是服务发给客户端的协议通道。服务端执行 `print("服务启动了")` 可能把非协议文本混进去，客户端便无法解析。写调试信息请用 stderr 或项目 logger；别把日志当作协议响应。

实验客户端能 print，因为它是给你看的终端入口；服务端 device_server.py 没有 print。这两个程序职责不同。

## 9. 自己改一处

把 labs 的第二条告警改成 `info`，运行客户端，确认传回两条数据且字段改变。再把 client 的 device_id 改成 999，观察 isError，不要把失败结果当作空设备。

**验收：** 能说出谁启动进程、谁 initialize、谁 list_tools、谁真正执行函数；知道工具调用 Schema、MCP 参数、函数参数分别位于哪一层。
