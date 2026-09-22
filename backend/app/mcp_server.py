"""独立 stdio MCP 服务：通过受 JWT 保护的 HTTP API 获取数据，不直连数据库。"""

import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("atlas-device-tools")


async def request(path: str, params=None):
    base = os.environ["ATLAS_API_URL"].rstrip("/")
    token = os.environ["ATLAS_ACCESS_TOKEN"]
    # 这是内部 API 通道。Windows 系统代理也可能接管 localhost，必须直连。
    async with httpx.AsyncClient(timeout=15, trust_env=False) as client:
        response = await client.get(
            base + path, params=params, headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code >= 400:
            raise ValueError(f"Atlas API 调用失败，状态码 {response.status_code}")
        return response.json()


@mcp.tool(structured_output=True)
async def get_device(device_id: int) -> dict[str, Any]:
    """获取设备登记信息；不等于实时状态。"""
    if device_id <= 0:
        raise ValueError("device_id 必须为正整数")
    return await request(f"/devices/{device_id}")


@mcp.tool(structured_output=True)
async def get_alarm(device_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """查询设备最近告警，最多三十条。"""
    if device_id <= 0 or not 1 <= limit <= 30:
        raise ValueError("参数越界")
    return await request(f"/devices/{device_id}/alarms", {"limit": limit})


@mcp.tool(structured_output=True)
async def search_manual(query: str) -> list[dict[str, Any]]:
    """检索 JWT 所属用户的手册，返回引用与页码。"""
    return await request("/knowledge/search", {"q": query, "top_k": 5})


if __name__ == "__main__":
    # stdout 是协议通道，禁止在此 print；诊断日志请写 stderr。
    mcp.run(transport="stdio")
