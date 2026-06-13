"""
In-memory BM25 keyword index for hybrid (sparse + dense) retrieval.

Qdrant 1.7.3 has no native sparse-vector fusion API, so BM25 is computed
in-memory over a collection's text payloads (fetched via
QdrantVectorStore.scroll_all_texts) and merged with dense vector results
before reranking.
"""

import re
from typing import Any, Dict, List

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"\w+")


class BM25Index:
    """Holds one BM25 index per Qdrant collection, built from scrolled payloads."""

    def __init__(self):
        self._indexes: Dict[str, BM25Okapi] = {}
        self._corpus_meta: Dict[str, List[Dict[str, Any]]] = {}

    def build(self, collection_name: str, points: List[Dict[str, Any]]) -> None:
        """
        Build (or rebuild) the BM25 index for a collection.

        Args:
            collection_name: Qdrant collection name
            points: List of payload dicts, each with at least a "text" key
        """
        tokenized = [self._tokenize(p.get("text", "")) for p in points]
        if not tokenized:
            self._indexes.pop(collection_name, None)
            self._corpus_meta.pop(collection_name, None)
            return

        self._indexes[collection_name] = BM25Okapi(tokenized)
        self._corpus_meta[collection_name] = points

    def search(self, collection_name: str, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Search a collection's BM25 index.

        Returns:
            Top `top_k` payload dicts, each with an added "bm25_score" key
        """
        index = self._indexes.get(collection_name)
        if index is None:
            return []

        scores = index.get_scores(self._tokenize(query))
        meta = self._corpus_meta[collection_name]
        ranked = sorted(zip(scores, meta), key=lambda x: x[0], reverse=True)

        return [{**m, "bm25_score": float(score)} for score, m in ranked[:top_k]]

    def is_indexed(self, collection_name: str) -> bool:
        return collection_name in self._indexes

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return _TOKEN_RE.findall(text.lower())
