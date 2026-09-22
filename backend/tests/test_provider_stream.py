import asyncio
import httpx
import pytest
from app.core.settings import Settings
from app.services.llm import LLMProvider, ProviderError


def test_compatible_sse_content_and_usage():
    async def run():
        provider = LLMProvider(Settings(llm_mode="compatible", _env_file=None))
        await provider.client.aclose()
        body = 'data: {"choices":[{"delta":{"content":"你好"}}]}\r\n\r\ndata: {"choices":[],"usage":{"output_tokens":2}}\n\ndata: [DONE]\n\n'
        provider.client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, text=body))
        )
        try:
            events = [
                item
                async for item in provider.stream([{"role": "user", "content": "hi"}])
            ]
            assert events == [
                {"type": "delta", "text": "你好"},
                {"type": "usage", "usage": {"output_tokens": 2}},
            ]
        finally:
            await provider.close()

    asyncio.run(run())


def test_truncated_sse_is_failure():
    async def run():
        provider = LLMProvider(Settings(llm_mode="compatible", _env_file=None))
        await provider.client.aclose()
        provider.client = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, text='data: {"choices":[]}\n\n')
            )
        )
        try:
            with pytest.raises(ProviderError, match="意外结束"):
                async for _ in provider.stream([{"role": "user", "content": "hi"}]):
                    pass
        finally:
            await provider.close()

    asyncio.run(run())
