"""MCP adapter：凭据仅传给本次受控子进程，不放在工具参数或模型消息中。"""

import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.core.settings import BACKEND_DIR


async def execute_mcp(name: str, arguments: dict, token: str, api_url: str):
    # 固定程序和模块，模型无法控制命令、路径或服务地址。
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE")
    }
    env.update(
        {
            "ATLAS_API_URL": api_url,
            "ATLAS_ACCESS_TOKEN": token,
            "PYTHONIOENCODING": "utf-8",
        }
    )
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        cwd=str(BACKEND_DIR),
        env=env,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            discovered = await session.list_tools()
            if name not in {tool.name for tool in discovered.tools}:
                raise ValueError("MCP 服务未提供所需工具")
            result = await session.call_tool(name, arguments)
            if result.isError:
                raise ValueError("MCP 工具执行失败")
            if result.structuredContent is not None:
                payload = result.structuredContent
                return payload.get("result", payload)
            text = "\n".join(
                block.text for block in result.content if block.type == "text"
            )
            return json.loads(text)
