"""BM25 → RRF 融合 → 可选 CrossEncoder；每一步独立，方便替换。"""

import math
from collections import Counter
from threading import Lock
from app.services.llm import tokens


def bm25(query: str, texts: list[str]) -> list[float]:
    documents = [Counter(tokens(text)) for text in texts]
    if not documents:
        return []
    lengths = [sum(doc.values()) for doc in documents]
    average = sum(lengths) / len(lengths) or 1
    frequencies = Counter(term for doc in documents for term in doc)
    scores = []
    for doc, length in zip(documents, lengths):
        score = 0.0
        for term in set(tokens(query)):
            frequency = doc[term]
            if not frequency:
                continue
            idf = math.log(
                1
                + (len(documents) - frequencies[term] + 0.5) / (frequencies[term] + 0.5)
            )
            score += (
                idf
                * frequency
                * 2.5
                / (frequency + 1.5 * (0.25 + 0.75 * length / average))
            )
        scores.append(score)
    return scores


def rrf(rankings: list[list[str]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, identifier in enumerate(dict.fromkeys(ranking), 1):
            scores[identifier] = scores.get(identifier, 0) + 1 / (60 + rank)
    return scores


class Reranker:
    def __init__(self, model: str):
        self.model_name = model
        self.model = None
        self.lock = Lock()

    def rank(self, query: str, candidates: list[dict]) -> list[dict]:
        if not self.model_name or not candidates:
            return candidates
        # 大模型依赖为可选项：uv sync --extra rerank；默认不下载模型。
        with self.lock:
            if self.model is None:
                from sentence_transformers import CrossEncoder

                self.model = CrossEncoder(self.model_name, trust_remote_code=False)
            scores = self.model.predict([(query, c["content"]) for c in candidates])
        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)
        return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
