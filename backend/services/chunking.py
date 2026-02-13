# backend/services/chunking.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class Chunk:
    chunk_id: str
    section: str
    start: int
    end: int
    text: str

def chunk_text(section: str, text: str, chunk_size: int = 4000, overlap: int = 400) -> List[Chunk]:
    """
    Splits text into overlapping chunks.
    chunk_size/overlap are in characters (fast + good enough for Day 4).
    """
    chunks: List[Chunk] = []
    n = len(text)
    i = 0
    idx = 0
    while i < n:
        j = min(i + chunk_size, n)
        chunk_str = text[i:j].strip()
        if chunk_str:
            chunks.append(
                Chunk(
                    chunk_id=f"{section}-{idx}",
                    section=section,
                    start=i,
                    end=j,
                    text=chunk_str,
                )
            )
            idx += 1
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks
