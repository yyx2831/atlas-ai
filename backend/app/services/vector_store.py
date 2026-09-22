"""Qdrant 本地与服务器模式；权限过滤必须在检索时执行。"""

import hashlib
from threading import RLock
from qdrant_client import QdrantClient, models
from app.core.settings import Settings


class VectorStore:
    def __init__(self, settings: Settings):
        key = f"{settings.embedding_mode}|{settings.embedding_base_url}|{settings.embedding_model}|{settings.embedding_dimension}"
        self.collection = "atlas_" + hashlib.sha256(key.encode()).hexdigest()[:16]
        self.lock = RLock()
        if settings.qdrant_url:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
                timeout=20,
                trust_env=False,  # 内部向量服务直连，避免系统代理截走 localhost
            )
        elif settings.qdrant_path == ":memory:":
            self.client = QdrantClient(":memory:")
        else:
            path = settings.qdrant_path or str(settings.data_dir / "vectors")
            self.client = QdrantClient(path=path)
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=models.VectorParams(
                    size=settings.embedding_dimension, distance=models.Distance.COSINE
                ),
            )

    def upsert(self, chunks: list, vectors: list, owner_id: int, document) -> None:
        points = [
            models.PointStruct(
                id=chunk.id,
                vector=vector,
                payload={
                    "owner_id": owner_id,
                    "document_id": document.id,
                    "product": document.product,
                    "version": document.version,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        with self.lock:
            self.client.upsert(self.collection, points, wait=True)

    def search(
        self, vector: list[float], owner_id: int, product: str, version: str, limit: int
    ):
        filters = [
            models.FieldCondition(
                key="owner_id", match=models.MatchValue(value=owner_id)
            )
        ]
        for key, value in [("product", product), ("version", version)]:
            if value:
                filters.append(
                    models.FieldCondition(key=key, match=models.MatchValue(value=value))
                )
        with self.lock:
            return self.client.query_points(
                self.collection,
                query=vector,
                query_filter=models.Filter(must=filters),
                limit=limit,
                with_payload=False,
            ).points

    def delete(self, document_id: str) -> None:
        with self.lock:
            self.client.delete(
                self.collection,
                models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
                wait=True,
            )

    def close(self):
        self.client.close()
