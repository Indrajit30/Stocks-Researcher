# backend/services/rag_pack.py
from __future__ import annotations
from typing import Dict, List, Tuple

def merge_citations(*citation_lists: List[Dict]) -> List[Dict]:
    # dedupe by (chunk_id, source_url)
    seen = set()
    out = []
    for lst in citation_lists:
        for c in lst:
            key = (c.get("chunk_id"), c.get("source_url"))
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
    return out

def bullets_from_answer(answer: str) -> List[str]:
    # your LLM returns "- " bullets already; normalize
    lines = [l.strip() for l in answer.splitlines() if l.strip()]
    bullets = []
    for l in lines:
        if l.startswith("- "):
            bullets.append(l[2:].strip())
        else:
            bullets.append(l)
    return bullets
