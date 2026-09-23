"""Day 23 独立练习：虚构数据的真实 MCP 服务；stdout 只传协议。"""

from typing import Any
from mcp.server.fastmcp import FastMCP
import tools_lab

mcp = FastMCP("device-mcp-server-lab")


@mcp.tool(structured_output=True)
async def get_device(device_id: int) -> dict[str, Any]:
    """查询虚构设备登记信息。"""
    args = tools_lab.DeviceInput(device_id=device_id)
    return tools_lab.get_device(args.device_id)


@mcp.tool(structured_output=True)
async def get_alarm(device_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """查询虚构设备的告警。"""
    args = tools_lab.AlarmInput(device_id=device_id, limit=limit)
    return tools_lab.get_alarm(args.device_id, args.limit)


@mcp.tool(structured_output=True)
async def search_manual(query: str) -> list[dict[str, Any]]:
    """查询虚构手册，返回来源与页码。"""
    args = tools_lab.ManualInput(query=query)
    return tools_lab.search_manual(args.query)


if __name__ == "__main__":
    mcp.run(transport="stdio")
