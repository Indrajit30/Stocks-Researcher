# backend/services/chunk_store.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

INDEX_DIR = Path("data/index")

def _meta_path(ticker: str, form: str, filing_date: str) -> Path:
    safe = f"{ticker.upper()}_{form}_{filing_date}"
    return INDEX_DIR / f"{safe}.meta.json"

def load_chunk_meta(ticker: str, form: str, filing_date: str) -> List[Dict]:
    path = _meta_path(ticker, form, filing_date)
    if not path.exists():
        return []
    return json.loads(path.read_text())

def get_chunk_by_id(
    ticker: str, form: str, filing_date: str, chunk_id: str
) -> Optional[Dict]:
    meta = load_chunk_meta(ticker, form, filing_date)
    for ch in meta:
        if ch.get("chunk_id") == chunk_id:
            return ch
    return None
