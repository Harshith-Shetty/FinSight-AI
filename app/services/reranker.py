"""
Cross-encoder reranking for retrieved RAG candidates.
"""

from typing import Any, Dict, List

from sentence_transformers import CrossEncoder


class Reranker:
    """
    Reranks retrieved chunks against the query using a cross-encoder model.

    Cross-encoders score a (query, document) pair jointly, which is far more
    accurate than comparing independently-computed embedding vectors —
    at the cost of being too slow to run over an entire collection, so it's
    used as a second-stage reranker over a small candidate set.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name, max_length=512)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Score and reorder candidates by relevance to the query.

        Args:
            query: The search query
            candidates: List of candidate chunks, each with a "text" key.
                        Mutated in place with a "rerank_score" key.
            top_k: Number of top candidates to return

        Returns:
            Top `top_k` candidates sorted by descending rerank_score
        """
        if not candidates:
            return []

        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)

        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)

        candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
        return candidates[:top_k]
