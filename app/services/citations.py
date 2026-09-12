"""Stable, JSON-safe source references shared by chat response modes."""

import math
from typing import Any


def build_citations(context: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep retrieval order so [n] always maps to the same excerpt.

    Only return citation fields; never expose arbitrary vector-store payloads.
    Page numbers are deliberately omitted because ingestion does not retain them.
    """
    citations = []
    for number, chunk in enumerate(context, 1):
        metadata = chunk.get("metadata") or {}
        document_id = chunk.get("document_id") or metadata.get("document_id")
        filename = metadata.get("filename") or chunk.get("filename")
        if not isinstance(filename, str) or filename.strip().lower() in ("", "unknown"):
            filename = f"Document {document_id}" if document_id else f"Source {number}"
        score = chunk.get("score", 0)
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0
        if not math.isfinite(score):
            score = 0.0
        chunk_id = metadata.get("chunk_id")
        citations.append({
            "citation_id": number,
            "document_id": str(document_id) if document_id is not None else None,
            "filename": filename,
            "text": chunk.get("text") or "",
            "source": chunk.get("source", "user"),
            "score": score,
            "metadata": {
                "filename": filename,
                "chunk_id": str(chunk_id) if chunk_id is not None else None,
            },
        })
    return citations
