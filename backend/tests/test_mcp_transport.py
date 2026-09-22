"""真实 stdio MCP 子进程测试；HTTP stub 验证令牌和三种返回类型。"""

import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from app.services.mcp_client import execute_mcp


def test_mcp_process_forwards_authenticated_http(monkeypatch):
    calls = []

    class API(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append((self.path, self.headers.get("Authorization")))
            if self.path.startswith("/knowledge/search"):
                data = [{"filename": "manual.md", "page": 2, "content": "检查网线"}]
            elif "/alarms" in self.path:
                data = [{"device_id": 7, "level": "warning"}]
            else:
                data = {"id": 7, "name": "Router-test"}
            content = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *args):
            pass

    # Internal calls must work even with an unusable process/system proxy.
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")
    server = ThreadingHTTPServer(("127.0.0.1", 0), API)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"

    async def run():
        device = await execute_mcp("get_device", {"device_id": 7}, "test-token", url)
        alarms = await execute_mcp(
            "get_alarm", {"device_id": 7, "limit": 2}, "test-token", url
        )
        sources = await execute_mcp(
            "search_manual", {"query": "断连"}, "test-token", url
        )
        assert device["id"] == 7
        assert alarms[0]["level"] == "warning"
        assert sources[0]["page"] == 2

    try:
        asyncio.run(run())
        assert len(calls) == 3
        assert all(token == "Bearer test-token" for _, token in calls)
        assert "limit=2" in calls[1][0]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
