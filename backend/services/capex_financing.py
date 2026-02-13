# backend/services/capex_financing.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, ConfigDict

from backend.services.retriever import retrieve_chunks


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: str
    doc_type: Optional[str] = None
    filing_date: Optional[str] = None
    url: Optional[str] = None

class Bullet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    text: str
    citations: List[Citation] = Field(default_factory=list)

class CapexFinancingOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capex_investment_bullets: List[Bullet] = Field(default_factory=list)
    financing_and_capital_allocation: List[Bullet] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)


SYSTEM = """You extract evidence from filing chunks.
Rules:
- Do not invent facts.
- Every bullet MUST include citations (chunk_id).
- If evidence is missing, omit the bullet and add a short item into missing[].
- Return ONLY valid JSON matching the schema. No markdown.
"""

def _queries(company_name: str, ticker: str) -> List[str]:
    return [
        f"{company_name} capital expenditures capex",
        f"{ticker} capital expenditures property and equipment",
        f"{company_name} liquidity and capital resources financing investments",
        f"{company_name} debt issuance credit facility notes payable",
        f"{company_name} share repurchase buyback authorization",
        f"{company_name} dividends dividend policy",
        f"{company_name} lease obligations financing leases operating leases",
        f"{company_name} capital allocation priorities",
    ]

def build_capex_financing_section(
    llm_client: Any,  # your LLMClient
    *,
    ticker: str,
    company_name: str,
    as_of: str,
    all_chunks: List[Dict],   # IMPORTANT: list of chunks you already built from filings
    top_k_each: int = 6,
    max_chunks_total: int = 30,
    max_retries: int = 2,
) -> Dict[str, Any]:
    # retrieve evidence chunks using your keyword retriever
    picked: List[Dict] = []
    seen = set()

    for q in _queries(company_name, ticker):
        got = retrieve_chunks(all_chunks, q, top_k=top_k_each) or []
        for ch in got:
            cid = ch.get("chunk_id")
            if cid and cid not in seen:
                seen.add(cid)
                picked.append(ch)
        if len(picked) >= max_chunks_total:
            break

    # Create prompt input: (keep text bounded)
    prompt_chunks = []
    for ch in picked[:max_chunks_total]:
        md = ch.get("metadata") or {}
        prompt_chunks.append({
            "chunk_id": ch.get("chunk_id"),
            "text": (ch.get("text") or "")[:2500],
            "doc_type": md.get("doc_type"),
            "filing_date": md.get("filing_date"),
            "url": md.get("url"),
        })

    user_payload = {
        "ticker": ticker,
        "as_of": as_of,
        "question": "How is the company financing investments (cash flow, debt, leases, buybacks/dividends)?",
        "retrieved_chunks": prompt_chunks,
        "output_schema": CapexFinancingOut.model_json_schema(),
        "requested_output": {
            "capex_investment_bullets": "3-6 bullets about capex/investment direction",
            "financing_and_capital_allocation": "3-8 bullets about financing sources + capital allocation (debt/leases/OCF/buybacks/dividends)",
        },
    }

    user = json.dumps(user_payload, ensure_ascii=False)
    last_err = None

    for attempt in range(max_retries + 1):
        raw = llm_client.summarize(SYSTEM, user)
        try:
            data = json.loads(raw)
            parsed = CapexFinancingOut.model_validate(data)
            out = parsed.model_dump()
            out["_meta"] = {"attempt": attempt, "chunks_used": len(prompt_chunks)}
            return out
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = f"attempt={attempt} err={str(e)[:300]}"
            user = user + "\n\nREPAIR: Output ONLY valid JSON matching schema. No extra keys."

    return {
        "capex_investment_bullets": [],
        "financing_and_capital_allocation": [],
        "missing": [last_err or "parse_failed"],
        "_meta": {"failed": True, "chunks_used": len(prompt_chunks)},
    }
