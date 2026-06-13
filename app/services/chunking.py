"""
Sentence- and section-aware text chunking utilities.

Replaces naive word-split chunking (which cuts mid-sentence) with chunking
that respects sentence boundaries, and optionally tags chunks with the SEC
filing section (e.g. "Item 1A. Risk Factors") they were extracted from.
"""

import re
from typing import List, Dict


# Matches sentence-ending punctuation followed by whitespace, while avoiding
# splitting on common abbreviations (Mr., Inc., U.S., e.g., etc.) followed by
# a lowercase word (likely mid-sentence) or a digit (likely a decimal number).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")

# SEC 10-K / 10-Q style section headers, e.g. "Item 1A. Risk Factors",
# "ITEM 7 - Management's Discussion and Analysis".
_SECTION_HEADER_RE = re.compile(
    r"(?im)^\s*(item\s+\d+[A-Za-z]?\.?\s*[-–—]?\s*[A-Za-z][^\n]{0,80})\s*$"
)

DEFAULT_SECTION = "general"


def _split_sentences(text: str) -> List[str]:
    """Split a block of text into sentences without breaking on common abbreviations."""
    text = text.strip()
    if not text:
        return []

    sentences = _SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if s.strip()]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs on blank lines, falling back to single newlines."""
    paragraphs = re.split(r"\n\s*\n", text)
    if len(paragraphs) == 1:
        paragraphs = text.split("\n")
    return [p.strip() for p in paragraphs if p.strip()]


def chunk_text_semantic(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks without cutting sentences in half.

    Sentences are packed greedily into chunks of up to `chunk_size` words.
    When a chunk is closed, the last `overlap` words are carried into the
    next chunk for continuity. A single sentence longer than `chunk_size`
    is word-split as a fallback.

    Args:
        text: Input text to chunk
        chunk_size: Target number of words per chunk
        overlap: Number of words to overlap between consecutive chunks

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    sentences: List[str] = []
    for paragraph in _split_paragraphs(text):
        sentences.extend(_split_sentences(paragraph))

    if not sentences:
        return []

    chunks: List[str] = []
    current_words: List[str] = []

    for sentence in sentences:
        sentence_words = sentence.split()

        if not sentence_words:
            continue

        # A single sentence longer than chunk_size: flush current chunk,
        # then word-split the oversized sentence on its own.
        if len(sentence_words) > chunk_size:
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = []
            for i in range(0, len(sentence_words), chunk_size - overlap):
                piece = sentence_words[i:i + chunk_size]
                if piece:
                    chunks.append(" ".join(piece))
            continue

        if len(current_words) + len(sentence_words) > chunk_size and current_words:
            chunks.append(" ".join(current_words))
            # Carry the overlap forward from the end of the closed chunk.
            current_words = current_words[-overlap:] if overlap > 0 else []

        current_words.extend(sentence_words)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def chunk_text_with_sections(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, str]]:
    """
    Chunk text while tagging each chunk with its SEC filing section.

    Walks the document line by line, tracking the most recently seen
    "Item N. <Title>" style header, and chunks the text between headers
    using `chunk_text_semantic`. Chunks before any recognized header are
    tagged with DEFAULT_SECTION.

    Args:
        text: Input text to chunk
        chunk_size: Target number of words per chunk
        overlap: Number of words to overlap between consecutive chunks

    Returns:
        List of {"text": chunk_text, "section": section_name} dicts
    """
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    sections: List[Dict[str, str]] = []
    current_section = DEFAULT_SECTION
    current_lines: List[str] = []

    for line in lines:
        match = _SECTION_HEADER_RE.match(line)
        if match:
            if current_lines:
                sections.append({"section": current_section, "text": "\n".join(current_lines)})
                current_lines = []
            current_section = match.group(1).strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({"section": current_section, "text": "\n".join(current_lines)})

    result: List[Dict[str, str]] = []
    for section in sections:
        for chunk in chunk_text_semantic(section["text"], chunk_size=chunk_size, overlap=overlap):
            result.append({"text": chunk, "section": section["section"]})

    return result
