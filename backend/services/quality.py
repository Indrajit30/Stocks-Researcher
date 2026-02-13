# backend/services/quality.py
from __future__ import annotations
from typing import Dict, List

def section_quality(citations: List[Dict]) -> Dict[str, float]:
    if not citations:
        return {"coverage": 0.0, "avg_score": 0.0}

    scores = [c.get("score") for c in citations if c.get("score") is not None]
    avg = float(sum(scores) / len(scores)) if scores else 0.0

    # coverage: 0..1 based on how many citations we have (cap at 6)
    coverage = min(1.0, len(citations) / 6.0)
    return {"coverage": coverage, "avg_score": avg}