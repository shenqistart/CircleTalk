"""混合检索/融合策略 - 自研实现，语义参考官方 langchain-postgres。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from langchain_core.documents import Document


def _normalize_scores(docs: Sequence[Document], is_distance_metric: bool) -> dict[str, float]:
    scores: list[float] = []
    ids: list[str] = []
    for doc in docs:
        metadata = doc.metadata
        doc_id = metadata.get("id")
        if doc_id is None:
            continue
        score = metadata.get("relevance_score", 0.0)
        try:
            score_val = float(score)
        except (TypeError, ValueError):
            continue
        ids.append(str(doc_id))
        scores.append(score_val)
    if not scores:
        return {}
    min_score, max_score = min(scores), max(scores)
    if max_score == min_score:
        normalized = [1.0] * len(scores)
    else:
        normalized = [(score - min_score) / (max_score - min_score) for score in scores]
        if is_distance_metric:
            normalized = [1.0 - value for value in normalized]
    return dict(zip(ids, normalized, strict=False))


def _clone_with_score(doc: Document, score: float) -> Document:
    metadata = doc.metadata.copy()
    metadata["relevance_score"] = score
    if doc_id := metadata.get("id"):
        metadata["id"] = doc_id
    return Document(page_content=doc.page_content, metadata=metadata)


class FusionStrategy(StrEnum):
    """混合检索分数融合策略。"""

    RRF = "rrf"
    WEIGHTED_SUM = "weighted_sum"


@dataclass(slots=True)
class HybridSearchConfig:
    """控制混合检索结果融合的配置。"""

    strategy: FusionStrategy = FusionStrategy.RRF
    vector_weight: float = 0.5
    fts_weight: float = 0.5
    rrf_k: float = 60
    fetch_top_k: int = 10
    is_distance_metric: bool = False

    def fuse(self, vector_docs: Sequence[Document], fts_docs: Sequence[Document]) -> list[Document]:
        if self.strategy == FusionStrategy.WEIGHTED_SUM:
            return self._weighted_sum_fusion(vector_docs, fts_docs)
        return self._rrf_fusion(vector_docs, fts_docs)

    def _weighted_sum_fusion(
        self,
        vector_docs: Sequence[Document],
        fts_docs: Sequence[Document],
    ) -> list[Document]:
        vector_scores = _normalize_scores(vector_docs, is_distance_metric=self.is_distance_metric)
        fts_scores = _normalize_scores(fts_docs, is_distance_metric=False)
        score_map: dict[str, float] = {}
        for doc_id, score in vector_scores.items():
            score_map[doc_id] = score * self.vector_weight
        for doc_id, score in fts_scores.items():
            score_map[doc_id] = score_map.get(doc_id, 0.0) + score * self.fts_weight
        doc_map: dict[str, Document] = {}
        for doc in list(vector_docs) + list(fts_docs):
            doc_id = doc.metadata.get("id")
            if doc_id is None:
                continue
            doc_map.setdefault(str(doc_id), doc)
        ranked = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
        fused_docs: list[Document] = []
        for doc_id, score in ranked[: self.fetch_top_k]:
            doc = doc_map.get(doc_id)
            if doc is None:
                continue
            fused_docs.append(_clone_with_score(doc, score))
        return fused_docs

    def _rrf_fusion(
        self,
        vector_docs: Sequence[Document],
        fts_docs: Sequence[Document],
    ) -> list[Document]:
        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}
        vector_sorted = sorted(
            vector_docs,
            key=lambda doc: float(doc.metadata.get("relevance_score", 0.0)),
            reverse=not self.is_distance_metric,
        )
        for rank, doc in enumerate(vector_sorted):
            doc_id = doc.metadata.get("id")
            if doc_id is None:
                continue
            key = str(doc_id)
            scores[key] = scores.get(key, 0.0) + self.vector_weight * (1.0 / (rank + self.rrf_k))
            doc_map.setdefault(key, doc)
        fts_sorted = sorted(
            fts_docs,
            key=lambda doc: float(doc.metadata.get("relevance_score", 0.0)),
            reverse=True,
        )
        for rank, doc in enumerate(fts_sorted):
            doc_id = doc.metadata.get("id")
            if doc_id is None:
                continue
            key = str(doc_id)
            scores[key] = scores.get(key, 0.0) + self.fts_weight * (1.0 / (rank + self.rrf_k))
            doc_map.setdefault(key, doc)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        fused_docs: list[Document] = []
        for doc_id, score in ranked[: self.fetch_top_k]:
            doc = doc_map.get(doc_id)
            if doc is None:
                continue
            fused_docs.append(_clone_with_score(doc, score))
        return fused_docs
