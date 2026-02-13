# backend/services/business_swot.py
from __future__ import annotations

from typing import Dict, List, Any

from backend.services.retriever import retrieve_chunks
from backend.services.llm import LLMClient

SYSTEM = """
You are a financial analyst.
You MUST answer strictly using the provided excerpts.
If the excerpts do not contain the answer, say "Not disclosed in this filing."
Do NOT use outside knowledge.
Return clean bullet points only.
"""


def _ask_from_filing_chunks(
    chunks: List[Dict[str, Any]],
    question: str,
    source_url: str,
    top_k: int = 8,
) -> Dict[str, Any]:
    retr = retrieve_chunks(chunks, question, top_k=top_k)

    if not retr:
        return {"bullets": ["Not disclosed in this filing."], "citations": []}

    context_blocks = []
    citations = []
    for ch in retr:
        context_blocks.append(f"[{ch['chunk_id']}]\n{ch['text']}")
        citations.append(
            {
                "chunk_id": ch["chunk_id"],
                "section": ch["section"],
                "source_url": source_url,
            }
        )

    user_prompt = f"""
Question:
{question}

SEC Filing Excerpts:
{chr(10).join(context_blocks)}

Answer in 5–8 bullet points.
"""

    llm = LLMClient()
    answer = llm.summarize(SYSTEM, user_prompt)

    # normalize answer into list of bullets (safe even if model returns plain text)
    bullets = []
    for line in (answer or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("-"):
            bullets.append(line[1:].strip())
        else:
            bullets.append(line)

    if not bullets:
        bullets = ["Not disclosed in this filing."]

    return {"bullets": bullets, "citations": citations}


def build_business_and_swot(
    ticker: str,
    filing_chunks: List[Dict[str, Any]],
    source_url: str,
) -> Dict[str, Any]:
    # Business understanding
    q_segments = "Describe the company's operating segments and how each generates revenue."
    q_revchar = "Describe revenue characteristics: recurring/subscription vs transactional, and any seasonality or cyclicality."
    q_geo = "Where does the company operate geographically? Mention key markets/regions if stated."
    q_kpis = "List the key performance indicators (KPIs) or operating metrics the company emphasizes."

    segments = _ask_from_filing_chunks(filing_chunks, q_segments, source_url, top_k=10)
    revchar = _ask_from_filing_chunks(filing_chunks, q_revchar, source_url, top_k=8)
    geos = _ask_from_filing_chunks(filing_chunks, q_geo, source_url, top_k=8)
    kpis = _ask_from_filing_chunks(filing_chunks, q_kpis, source_url, top_k=10)

    # SWOT
    s_strengths = _ask_from_filing_chunks(
        filing_chunks,
        "From this filing, what are the company's strengths or competitive advantages?",
        source_url,
        top_k=10,
    )
    s_weaknesses = _ask_from_filing_chunks(
        filing_chunks,
        "From this filing, what are the company's weaknesses, constraints, or pressure points?",
        source_url,
        top_k=10,
    )
    s_opportunities = _ask_from_filing_chunks(
        filing_chunks,
        "From this filing, what opportunities or growth drivers are described (new investments, products, markets)?",
        source_url,
        top_k=10,
    )
    s_threats = _ask_from_filing_chunks(
        filing_chunks,
        "From this filing, what threats or major risks are highlighted (competition, regulation, cyber, macro, etc.)?",
        source_url,
        top_k=12,
    )

    return {
        "business": {
            "segments": segments,
            "revenue_characteristics": revchar,
            "geographies": geos,
            "kpis": kpis,
        },
        "swot": {
            "strengths": s_strengths,
            "weaknesses": s_weaknesses,
            "opportunities": s_opportunities,
            "threats": s_threats,
        },
    }
