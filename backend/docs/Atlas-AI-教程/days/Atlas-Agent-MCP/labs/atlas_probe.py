"""Day 24：登录自己的 Atlas，验证真实 API/MCP；默认仅查询。"""

import argparse
import asyncio
import getpass
import json
from pathlib import Path
import sys
import httpx


async def main(args):
    backend = Path(args.backend).resolve()
    if not (backend / "app/mcp_server.py").exists():
        raise ValueError("backend 路径没有 app/mcp_server.py")
    sys.path.insert(0, str(backend))
    from app.services.mcp_client import execute_mcp

    async with httpx.AsyncClient(
        base_url=args.url.rstrip("/"), timeout=120, trust_env=False
    ) as client:
        response = await client.post(
            "/auth/login",
            json={"email": args.email, "password": getpass.getpass("Atlas 密码：")},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        for name, values in [
            ("get_device", {"device_id": args.device_id}),
            ("get_alarm", {"device_id": args.device_id, "limit": 3}),
            ("search_manual", {"query": "设备断连 ERR-1007"}),
        ]:
            async with asyncio.timeout(30):
                result = await execute_mcp(name, values, token, args.url)
            print(name, json.dumps(result, ensure_ascii=False, indent=2))
        if args.run_agent:
            # 此选项会创建一条自己的分析记录，并使用后端配置的模型。
            response = await client.post(
                "/agent/runs",
                headers=headers,
                json={
                    "question": "设备频繁断连，请结合告警与手册给出排查方向。",
                    "device_id": args.device_id,
                    "engine": args.engine,
                    "transport": "mcp",
                },
            )
            response.raise_for_status()
            result = response.json()
            print("Agent", json.dumps(result, ensure_ascii=False, indent=2))
            if any(not step["result"]["ok"] for step in result["steps"]):
                raise RuntimeError("任务已返回，但存在失败的工具；请逐项查看 steps")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default="E:/Codes/atlas-ai/backend")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", required=True)
    parser.add_argument("--device-id", type=int, required=True)
    parser.add_argument("--run-agent", action="store_true")
    parser.add_argument("--engine", choices=["loop", "graph"], default="loop")
    asyncio.run(main(parser.parse_args()))
