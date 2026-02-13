# backend/services/filing_summary_vector.py
from __future__ import annotations
from typing import Dict, List

from backend.services.llm import LLMClient
from backend.services.embeddings import EmbeddingsClient
from backend.services.vector_index import build_or_load_index, search_index

SYSTEM_PROMPT = """
You are a financial analyst.
You MUST answer strictly using the provided excerpts.
If the excerpts do not contain the answer, say "Not disclosed in this filing."
Do NOT use outside knowledge.
"""

def summarize_filing_vector(
    ticker: str,
    form: str,
    filing_date: str,
    chunks: List[Dict],
    question: str,
    source_url: str,
    force_reindex: bool = False,
) -> Dict:
    index, meta = build_or_load_index(
        ticker=ticker,
        form=form,
        filing_date=filing_date,
        chunks=chunks,
        force_rebuild=force_reindex,
    )

    q_emb = EmbeddingsClient().embed_texts([question])[0]
    retrieved = search_index(index, meta, q_emb, top_k=6)

    if not retrieved:
        return {"answer": "Not disclosed in this filing.", "citations": []}

    context_blocks = []
    citations = []
    for r in retrieved:
        context_blocks.append(f"[{r['chunk_id']}]\n{r['text']}")
        citations.append({
            "chunk_id": r["chunk_id"],
            "section": r["section"],
            "score": r["score"],
            "source_url": source_url,
        })

    user_prompt = f"""
Question:
{question}

SEC Filing Excerpts:
{chr(10).join(context_blocks)}

Answer in 6–10 bullet points.
Prefer numeric facts when available.
"""

    answer = LLMClient().summarize(SYSTEM_PROMPT, user_prompt)
    return {"answer": answer, "citations": citations}
