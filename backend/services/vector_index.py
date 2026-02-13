from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import faiss

from backend.services.embeddings import EmbeddingsClient

INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def _paths(ticker: str, form: str, filing_date: str) -> Tuple[Path, Path]:
    safe = f"{ticker.upper()}_{form}_{filing_date}"
    return INDEX_DIR / f"{safe}.faiss", INDEX_DIR / f"{safe}.meta.json"

def build_or_load_index(
    ticker: str,
    form: str,
    filing_date: str,
    chunks: List[Dict],
    force_rebuild: bool = False,
) -> Tuple[faiss.Index, List[Dict]]:
    """
    Builds a FAISS index over chunk embeddings.
    Saves:
      - .faiss index
      - .meta.json chunk metadata (chunk_id, section, text)
    """
    index_path, meta_path = _paths(ticker, form, filing_date)

    if (not force_rebuild) and index_path.exists() and meta_path.exists():
        index = faiss.read_index(str(index_path))
        meta = json.loads(meta_path.read_text())
        return index, meta

    # embed all chunks
    texts = [c["text"] for c in chunks]
    emb = EmbeddingsClient().embed_texts(texts)
    vectors = np.array(emb, dtype="float32")

    # cosine similarity = inner product on normalized vectors
    faiss.normalize_L2(vectors)

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(chunks, indent=2))

    return index, chunks

def search_index(
    index: faiss.Index,
    meta: List[Dict],
    query_embedding: List[float],
    top_k: int = 6,
) -> List[Dict]:
    q = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(q)
    scores, ids = index.search(q, top_k)

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        ch = meta[idx]
        results.append({
            "score": float(score),
            "chunk_id": ch["chunk_id"],
            "section": ch["section"],
            "text": ch["text"],
        })
    return results
