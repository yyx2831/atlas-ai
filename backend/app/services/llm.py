"""兼容 API 与演示模型共用接口；业务层不依赖某一家厂商 SDK。"""

import asyncio
import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import AsyncIterator

import httpx
from app.core.settings import Settings


class ProviderError(Exception):
    """给用户的消息不包含 URL 密钥或供应商原始响应正文。"""


def tokens(text: str) -> list[str]:
    """教学分词：英文/编号保留，中文使用单字和相邻双字。"""
    words = re.findall(r"[a-z0-9_-]+|[\u4e00-\u9fff]", text.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]+", text)
    return words + [part[i : i + 2] for part in chinese for i in range(len(part) - 1)]


class LLMProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            timeout=settings.llm_timeout,
            limits=httpx.Limits(max_connections=20),
            trust_env=settings.model_trust_env,
        )

    async def close(self):
        await self.client.aclose()

    def headers(self, key: str) -> dict:
        return {"Authorization": f"Bearer {key}"} if key else {}

    async def post(self, url: str, body: dict, key: str) -> dict:
        # 仅重试明确拒绝处理的 429/503；不重试写操作，也不无限重试。
        for attempt in range(2):
            try:
                response = await self.client.post(
                    url, json=body, headers=self.headers(key)
                )
                if response.status_code in (429, 503) and attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as exc:
                raise ProviderError("模型服务超时，请稍后重试") from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise ProviderError(
                    "模型服务请求失败，请检查模型名称与连接配置"
                ) from exc
        raise ProviderError("模型服务暂不可用")

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        s = self.settings
        if s.llm_mode == "demo":
            return self.demo_response(messages, tools)
        body = {
            "model": s.llm_model,
            "messages": messages,
            "max_tokens": s.llm_max_tokens,
        }
        if tools:
            body["tools"] = tools
        result = await self.post(
            s.llm_base_url.rstrip("/") + "/chat/completions", body, s.llm_api_key
        )
        try:
            return result["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("模型返回格式不符合聊天接口约定") from exc

    async def stream(self, messages: list[dict]) -> AsyncIterator[dict]:
        s = self.settings
        if s.llm_mode == "demo":
            answer = self.demo_response(messages)["content"]
            for start in range(0, len(answer), 16):
                await asyncio.sleep(0.015)
                yield {"type": "delta", "text": answer[start : start + 16]}
            return
        body = {
            "model": s.llm_model,
            "messages": messages,
            "max_tokens": s.llm_max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        try:
            async with self.client.stream(
                "POST",
                s.llm_base_url.rstrip("/") + "/chat/completions",
                json=body,
                headers=self.headers(s.llm_api_key),
            ) as response:
                response.raise_for_status()
                data_lines = []
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                    elif not line and data_lines:
                        data = "\n".join(data_lines)
                        data_lines = []
                        if data == "[DONE]":
                            return
                        event = json.loads(data)
                        if event.get("error"):
                            raise ProviderError("模型流返回错误")
                        if event.get("usage"):
                            yield {"type": "usage", "usage": event["usage"]}
                        choices = event.get("choices", [])
                        if choices:
                            text = choices[0].get("delta", {}).get("content")
                            if isinstance(text, str) and text:
                                yield {"type": "delta", "text": text}
                raise ProviderError("模型流意外结束，没有收到结束标记")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ProviderError("模型流连接失败或格式错误") from exc

    def demo_response(self, messages: list[dict], tools=None) -> dict:
        """确定性演示，不伪装成真实大模型。Agent 模式依次演示三个只读工具。"""
        if tools:
            used = [m.get("name") for m in messages if m["role"] == "tool"]
            request = json.loads(
                next(m["content"] for m in messages if m["role"] == "user")
            )
            calls = [
                ("get_device", {"device_id": request["device_id"]}),
                ("get_alarm", {"device_id": request["device_id"], "limit": 10}),
                ("search_manual", {"query": request["question"]}),
            ]
            for name, arguments in calls:
                if name not in used:
                    return {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": f"call-{len(used)}",
                                "type": "function",
                                "function": {
                                    "name": name,
                                    "arguments": json.dumps(
                                        arguments, ensure_ascii=False
                                    ),
                                },
                            }
                        ],
                    }
            evidence = "\n".join(
                f"{m['name']}：{m['content'][:1400]}"
                for m in messages
                if m["role"] == "tool"
            )
            return {
                "role": "assistant",
                "content": "【演示模式】已完成设备、告警与手册查询。以下为实际工具返回，尚不能据此确定故障根因。\n"
                + evidence,
            }
        context = next(
            (
                m["content"]
                for m in messages
                if m["role"] == "system" and "检索资料" in m["content"]
            ),
            "",
        )
        answer = (
            "【演示模式】以下摘录来自你的文档，演示引用与流式展示，不是模型推理结论。\n"
            + context.split("检索资料：", 1)[-1][:2200]
            if context
            else "【演示模式】聊天链路已连接。上传设备手册后可以体验知识检索，或在配置中连接真实模型。"
        )
        return {"role": "assistant", "content": answer}

    async def embed(self, texts: list[str]) -> list[list[float]]:
        s = self.settings
        if s.embedding_mode == "demo":
            vectors = []
            for text in texts:
                vector = [0.0] * s.embedding_dimension
                for term, count in Counter(tokens(text)).items():
                    index = int.from_bytes(
                        hashlib.sha256(term.encode()).digest()[:8], "big"
                    ) % len(vector)
                    vector[index] += count
                norm = math.sqrt(sum(x * x for x in vector)) or 1
                vectors.append([x / norm for x in vector])
            return vectors
        result = await self.post(
            s.embedding_base_url.rstrip("/") + "/embeddings",
            {"model": s.embedding_model, "input": texts},
            s.embedding_api_key,
        )
        try:
            entries = sorted(result["data"], key=lambda item: item["index"])
            if [item["index"] for item in entries] != list(range(len(texts))):
                raise ValueError("embedding indices do not match input")
            vectors = [item["embedding"] for item in entries]
            if any(
                len(v) != s.embedding_dimension or not all(math.isfinite(x) for x in v)
                for v in vectors
            ):
                raise ValueError("invalid vector dimension or values")
            return vectors
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(
                "Embedding 返回维度/数量不匹配，请检查 EMBEDDING_DIMENSION"
            ) from exc
