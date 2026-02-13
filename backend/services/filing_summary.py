# backend/services/filing_summary.py
from __future__ import annotations
from typing import Dict, List

from backend.services.retriever import retrieve_chunks
from backend.services.llm import LLMClient

SYSTEM_PROMPT = """
You are a financial analyst.
You MUST answer strictly using the provided excerpts.
If the excerpts do not contain the answer, say "Not disclosed in this filing."
Do NOT use outside knowledge.
"""

def summarize_filing(
    chunks: List[Dict],
    question: str,
    source_url: str,
) -> Dict:
    retr = retrieve_chunks(chunks, question, top_k=6)

    if not retr:
        return {
            "answer": "Not disclosed in this filing.",
            "citations": [],
        }

    context_blocks = []
    citations = []

    for ch in retr:
        context_blocks.append(
            f"[{ch['chunk_id']}]\n{ch['text']}"
        )
        citations.append({
            "chunk_id": ch["chunk_id"],
            "section": ch["section"],
            "source_url": source_url,
        })

    user_prompt = f"""
Question:
{question}

SEC Filing Excerpts:
{chr(10).join(context_blocks)}

Answer in 5–8 bullet points.
"""

    llm = LLMClient()
    answer = llm.summarize(SYSTEM_PROMPT, user_prompt)

    return {
        "answer": answer,
        "citations": citations,
    }
