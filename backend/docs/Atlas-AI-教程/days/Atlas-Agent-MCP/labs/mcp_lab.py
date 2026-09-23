"""Day 23：真实启动 MCP 子进程，不需要 API Key 或 FastAPI。"""

import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=sys.executable, args=[str(Path(__file__).with_name("device_server.py"))]
    )
    async with asyncio.timeout(25):
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listing = await session.list_tools()
                print("可用工具：", [tool.name for tool in listing.tools])
                assert {t.name for t in listing.tools} == {
                    "get_device",
                    "get_alarm",
                    "search_manual",
                }
                for name, arguments in [
                    ("get_device", {"device_id": 1}),
                    ("get_alarm", {"device_id": 1, "limit": 2}),
                    ("search_manual", {"query": "ERR-1007"}),
                ]:
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, result
                    assert result.structuredContent is not None
                    payload = result.structuredContent
                    value = payload.get("result", payload)
                    print(name, json.dumps(value, ensure_ascii=False))
                    if name == "get_device":
                        assert value["id"] == 1
                    else:
                        assert isinstance(value, list) and value
                rejected = await session.call_tool("get_device", {"device_id": 999})
                assert rejected.isError
                print("不存在的设备：isError=True（符合预期）")


if __name__ == "__main__":
    asyncio.run(main())
