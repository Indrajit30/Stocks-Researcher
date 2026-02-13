# backend/services/retriever.py
from __future__ import annotations
from typing import List, Dict
import re

def score_chunk(chunk_text: str, query_terms: List[str]) -> int:
    """
    Very simple relevance scoring:
    +1 per keyword hit (case-insensitive)
    """
    text = chunk_text.lower()
    return sum(1 for term in query_terms if term in text)

def retrieve_chunks(
    chunks: List[Dict],
    query: str,
    top_k: int = 6,
) -> List[Dict]:
    """
    Retrieve top-k relevant chunks using keyword overlap.
    Deterministic and debuggable (perfect before embeddings).
    """
    terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 3]

    scored = []
    for ch in chunks:
        score = score_chunk(ch["text"], terms)
        if score > 0:
            scored.append((score, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [ch for _, ch in scored[:top_k]]