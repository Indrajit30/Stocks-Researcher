# backend/services/one_pager_summary.py
from __future__ import annotations

import json
from typing import Any, Dict, Optional, List

from pydantic import BaseModel, Field, ValidationError, ConfigDict


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: str
    doc_type: Optional[str] = None
    filing_date: Optional[str] = None
    url: Optional[str] = None

class OnePagerBullet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    text: str
    citations: List[Citation] = Field(default_factory=list)

class OnePageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_of: str
    bullets: List[OnePagerBullet] = Field(..., min_length=6, max_length=10)
    notes: Optional[str] = None


SYSTEM_PROMPT = """You are a finance analyst assistant.
Hard rules:
- DO NOT invent numbers. Only restate numbers present in the input.
- If a claim is supported by filing RAG chunks, attach citations with chunk_id.
- If evidence is missing, explicitly say "Not found in filings" (do not guess).
- Return ONLY valid JSON matching the provided schema. No markdown.
"""

def generate_one_page_summary(
    llm_client: Any,  # your LLMClient
    *,
    ticker: str,
    as_of: str,
    company_profile: Dict[str, Any],
    metrics: Dict[str, Any],
    rag_sections: Dict[str, Any],  # your existing 4 RAG sections
    max_retries: int = 2,
) -> Dict[str, Any]:
    user_payload = {
        "ticker": ticker,
        "as_of": as_of,
        "company_profile": company_profile,
        "metrics": metrics,
        "rag_sections": rag_sections,
        "instructions": {
            "target": "Create ~8 executive bullets that summarize the full report: business, key metrics, quarter highlights, capex/investments, financing/capital allocation, SWOT, risks, valuation vs sector.",
            "style": "concise, 1-2 lines per bullet",
        },
        "output_schema": OnePageSummary.model_json_schema(),
    }

    user = json.dumps(user_payload, ensure_ascii=False)
    last_err = None

    for attempt in range(max_retries + 1):
        raw = llm_client.summarize(SYSTEM_PROMPT, user)

        try:
            data = json.loads(raw)
            parsed = OnePageSummary.model_validate(data)
            out = parsed.model_dump()
            out["_meta"] = {"attempt": attempt}
            return out
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = f"attempt={attempt} err={str(e)[:300]}"
            # tighten repair prompt
            user = user + "\n\nREPAIR: Return ONLY valid JSON matching schema. No extra keys."

    return {
        "as_of": as_of,
        "bullets": [
            {"label": "Error", "text": "One-page summary generation failed.", "citations": []}
        ],
        "notes": last_err or "Unknown error",
        "_meta": {"failed": True},
    }
