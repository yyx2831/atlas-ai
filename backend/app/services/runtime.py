"""应用生命周期资源：只创建一次模型 HTTP 客户端、向量库与限流器。"""

import hashlib
import time
from collections import deque
from threading import Lock
from fastapi import HTTPException
from redis import Redis
from app.core.settings import Settings
from app.services.llm import LLMProvider
from app.services.vector_store import VectorStore
from app.services.retrieval import Reranker


class LoginLimiter:
    def __init__(self, url: str):
        self.redis = (
            Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
            if url
            else None
        )
        self.entries: dict[str, deque] = {}
        self.lock = Lock()

    def check(self, address: str):
        key = "atlas:login:" + hashlib.sha256(address.encode()).hexdigest()
        if self.redis:
            try:
                count = self.redis.eval(
                    "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",
                    1,
                    key,
                )
            except Exception as exc:
                raise HTTPException(503, "登录限流服务暂不可用") from exc
        else:
            with self.lock:
                now = time.monotonic()
                for old in list(self.entries):
                    if not self.entries[old] or self.entries[old][-1] < now - 60:
                        del self.entries[old]
                if key not in self.entries and len(self.entries) >= 10000:
                    raise HTTPException(429, "登录请求过多")
                queue = self.entries.setdefault(key, deque())
                while queue and queue[0] < now - 60:
                    queue.popleft()
                if len(queue) >= 10:
                    raise HTTPException(429, "登录过于频繁，请一分钟后再试")
                queue.append(now)
                count = len(queue)
        if count > 10:
            raise HTTPException(429, "登录过于频繁，请一分钟后再试")


class Runtime:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.vectors = VectorStore(settings)
        self.llm = LLMProvider(settings)
        self.reranker = Reranker(settings.rerank_model)
        self.limiter = LoginLimiter(settings.redis_url)
        # 上传/重建串行化，避免重复上传和删除同时修改同一索引（单进程学习版）。
        import asyncio

        self.index_lock = asyncio.Lock()

    async def close(self):
        await self.llm.close()
        self.vectors.close()
        if self.limiter.redis:
            self.limiter.redis.close()
