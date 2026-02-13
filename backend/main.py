from __future__ import annotations

import os
import json
from datetime import date
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.services.error import safe_step
from backend.schemas.equity_report import EquityReport, ReportSection

from backend.services.cache import make_key, load_cache, save_cache
from backend.services.metrics import SeriesPoint, revenue_cagr, operating_margin, net_debt_to_ebitda
from backend.services.providers import get_company_profile, get_financial_snapshot

from backend.services.filings import get_latest_filing_html
from backend.services.html_to_text import html_to_clean_text
from backend.services.sectioner import split_into_sections
from backend.services.chunking import chunk_text
from backend.services.quality import section_quality

from backend.services.filing_summary_vector import summarize_filing_vector
from backend.services.rag_pack import bullets_from_answer

from backend.services.chunk_store import get_chunk_by_id
from backend.services.pdf_report import build_equity_pdf

from backend.services.news import get_stock_news
from backend.services.llm import LLMClient

from backend.services.business_swot import build_business_and_swot

from backend.services.capex_financing import build_capex_financing_section
from backend.services.one_pager_summary import generate_one_page_summary

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Stock Intelligence API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReportRequest(BaseModel):
    ticker: str = Field(..., examples=["MSFT"])
    refresh: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/report")
def report(req: ReportRequest):
    ticker = req.ticker.upper()
    asof = date.today().isoformat()

    cache_key = make_key("report_minimal", ticker, asof=asof)

    if not req.refresh:
        cached = load_cache(cache_key, ttl_seconds=24 * 3600)
        if cached:
            return {"cached": True, **cached}

    profile = get_company_profile(ticker)
    fin = get_financial_snapshot(ticker)

    series = [
        SeriesPoint(year=int(x["year"]), value=float(x["value"]))
        for x in fin.get("revenue_series", [])
        if x.get("year") is not None and x.get("value") is not None
    ]
    latest = fin.get("latest", {}) or {}

    cagr_10y = revenue_cagr(series, years=10) if series else None

    op_margin: Optional[float] = None
    if latest.get("revenue") is not None and latest.get("operating_income") is not None:
        op_margin = operating_margin(float(latest["operating_income"]), float(latest["revenue"]))

    nd_ebitda: Optional[float] = None
    if latest.get("total_debt") is not None and latest.get("cash_and_equiv") is not None and latest.get("ebitda") is not None:
        nd_ebitda = net_debt_to_ebitda(
            float(latest["total_debt"]),
            float(latest["cash_and_equiv"]),
            float(latest["ebitda"]),
        )

    payload = {
        "asof": asof,
        "company": profile,
        "metrics": {
            "revenue_cagr_10y": cagr_10y,
            "operating_margin": op_margin,
            "net_debt_to_ebitda": nd_ebitda,
        },
    }

    save_cache(cache_key, payload)
    return {"cached": False, **payload}


@app.get("/report")
def report_get(ticker: str = Query(...), refresh: bool = Query(False)):
    return report(ReportRequest(ticker=ticker, refresh=refresh))


# -------------------------
# Filing endpoints (keep)
# -------------------------
@app.get("/filings/latest")
def latest_filing(ticker: str, form: str = "10-Q"):
    filing = get_latest_filing_html(ticker, form_type=form)
    html = filing["html"]
    preview = html[:5000]
    return {
        "ticker": ticker.upper(),
        "form": filing["form"],
        "filing_date": filing["filing_date"],
        "url": filing["url"],
        "html_preview": preview,
        "html_chars": len(html),
    }


@app.get("/filings/latest/chunks")
def latest_filing_chunks(ticker: str, form: str = "10-Q", refresh: bool = False):
    ticker = ticker.upper()
    asof = date.today().isoformat()

    cache_key = make_key(f"filing_chunks_{form}", ticker, asof=asof)
    if not refresh:
        cached = load_cache(cache_key, ttl_seconds=7 * 24 * 3600)
        if cached:
            return {"cached": True, **cached}

    filing = get_latest_filing_html(ticker, form_type=form)
    clean = html_to_clean_text(filing["html"])
    sections = split_into_sections(clean)

    all_chunks = []
    for section_name, section_text in sections.items():
        chunks = chunk_text(section_name, section_text, chunk_size=4000, overlap=400)
        for c in chunks:
            all_chunks.append({
                "chunk_id": c.chunk_id,
                "section": c.section,
                "start": c.start,
                "end": c.end,
                "text": c.text,
            })

    payload = {
        "ticker": ticker,
        "form": filing["form"],
        "filing_date": filing["filing_date"],
        "source_url": filing["url"],
        "clean_chars": len(clean),
        "sections_found": list(sections.keys()),
        "num_chunks": len(all_chunks),
        "chunks": all_chunks[:50],
    }

    save_cache(cache_key, payload)
    return {"cached": False, **payload}


# -------------------------
# MAIN: Equity report (extended)
# -------------------------
@app.get("/equity_report", response_model=EquityReport)
def equity_report(ticker: str, refresh: bool = False, reindex: bool = False):
    ticker = ticker.upper()
    asof = date.today().isoformat()
    errors = []

    cache_key = make_key("equity_report_v2", ticker, asof=asof)
    if not refresh:
        cached = load_cache(cache_key, ttl_seconds=6 * 3600)
        if cached:
            return {"ticker": ticker, **cached}

    # 1) Company profile + snapshot metrics
    profile = safe_step(
        "company_profile",
        lambda: get_company_profile(ticker),
        errors,
        default={},
    )

    fin = safe_step(
        "financial_snapshot",
        lambda: get_financial_snapshot(ticker),
        errors,
        default={},
    )

    series = [
        SeriesPoint(year=int(x["year"]), value=float(x["value"]))
        for x in fin.get("revenue_series", [])
        if x.get("year") is not None and x.get("value") is not None
    ]
    latest = fin.get("latest", {}) or {}

    # Your newer usage is revenue_cagr(series, max_years=10) -> (value, years)
    cagr_result = revenue_cagr(series, max_years=10) if series else None
    if cagr_result:
        cagr_value, cagr_years = cagr_result
    else:
        cagr_value, cagr_years = None, None

    op_margin = None
    if latest.get("revenue") is not None and latest.get("operating_income") is not None:
        op_margin = operating_margin(float(latest["operating_income"]), float(latest["revenue"]))

    nd_ebitda = None
    if latest.get("total_debt") is not None and latest.get("cash_and_equiv") is not None and latest.get("ebitda") is not None:
        nd_ebitda = net_debt_to_ebitda(
            float(latest["total_debt"]),
            float(latest["cash_and_equiv"]),
            float(latest["ebitda"]),
        )

    metrics = {
        "revenue_cagr": cagr_value,
        "revenue_cagr_years": cagr_years,
        "operating_margin": op_margin,
        "net_debt_to_ebitda": nd_ebitda,
    }

    # 2) Latest filing chunks (build once)
    filing = get_latest_filing_html(ticker, form_type="10-Q")
    clean = html_to_clean_text(filing["html"])
    filing_sections = split_into_sections(clean)

    all_chunks = []
    for section, text in filing_sections.items():
        for c in chunk_text(section, text):
            all_chunks.append({"chunk_id": c.chunk_id, "section": c.section, "text": c.text})

    biz_swot = safe_step(
        "business_swot",
        lambda: build_business_and_swot(
            ticker=ticker,
            filing_chunks=all_chunks,
            source_url=filing["url"],
        ),
        errors,
        default={"business": None, "swot": None},
    )


    # 3) RAG pack questions (existing)
    q1 = "What were the key financial highlights this quarter? Include revenue, operating income, net income, EPS, and cash flow if disclosed."
    q2 = "What did the company say about capital expenditures, investing activities, or major investment plans (e.g., data centers, infrastructure)?"
    q3 = "What were the key risks or uncertainties discussed this quarter?"
    q4 = "What were the major segment or product line drivers (e.g., cloud, productivity, devices), and what changed year-over-year?"

    s1 = summarize_filing_vector(ticker, filing["form"], filing["filing_date"], all_chunks, q1, filing["url"], force_reindex=reindex)
    s2 = summarize_filing_vector(ticker, filing["form"], filing["filing_date"], all_chunks, q2, filing["url"], force_reindex=False)
    s3 = summarize_filing_vector(ticker, filing["form"], filing["filing_date"], all_chunks, q3, filing["url"], force_reindex=False)
    s4 = summarize_filing_vector(ticker, filing["form"], filing["filing_date"], all_chunks, q4, filing["url"], force_reindex=False)

    sec1 = ReportSection(
        title="Quarter highlights",
        bullets=bullets_from_answer(s1["answer"]),
        citations=s1["citations"],
    )
    sec2 = ReportSection(
        title="Investment & CAPEX signals",
        bullets=bullets_from_answer(s2["answer"]),
        citations=s2["citations"],
    )
    sec3 = ReportSection(
        title="Risks mentioned in filing",
        bullets=bullets_from_answer(s3["answer"]),
        citations=s3["citations"],
    )
    sec4 = ReportSection(
        title="Segment / product drivers",
        bullets=bullets_from_answer(s4["answer"]),
        citations=s4["citations"],
    )

    quality = {
        "Quarter highlights": section_quality(s1["citations"]),
        "Investment & CAPEX signals": section_quality(s2["citations"]),
        "Risks mentioned in filing": section_quality(s3["citations"]),
        "Segment / product drivers": section_quality(s4["citations"]),
    }

    # 4) Latest news
    news_items = safe_step(
        "news",
        lambda: get_stock_news(ticker, days=7, limit=15),
        errors,
        default=[],
    )

    news_block = {"window_days": 7, "articles": news_items[:8]}

    llm = LLMClient()

    one_page_summary = generate_one_page_summary(
        llm_client=llm,
        ticker=ticker,
        as_of=asof,
        company_profile=profile,
        metrics=metrics,
        rag_sections={
            "quarter_highlights": {
                "bullets": sec1.bullets,
                "citations": [c.model_dump() for c in sec1.citations],
            },
            "capex_signals": {
                "bullets": sec2.bullets,
                "citations": [c.model_dump() for c in sec2.citations],
            },
            "risks": {
                "bullets": sec3.bullets,
                "citations": [c.model_dump() for c in sec3.citations],
            },
            "segment_drivers": {
                "bullets": sec4.bullets,
                "citations": [c.model_dump() for c in sec4.citations],
            },
            "business": biz_swot.get("business", {}),
            "swot": biz_swot.get("swot", {}),
            "news": news_block,
        },
    )
    # -------------------------
    # NEW (4): CAPEX & Financing lens section
    # -------------------------
    capex_financing = {}
    try:
        llm = LLMClient()  # uses OPENAI_API_KEY
        capex_financing = build_capex_financing_section(
            llm_client=llm,
            ticker=ticker,
            company_name=(profile.get("name") or profile.get("companyName") or ticker),
            as_of=asof,
            all_chunks=all_chunks,
        )
    except Exception as e:
        capex_financing = {
            "capex_investment_bullets": [],
            "financing_and_capital_allocation": [],
            "missing": [f"capex_financing_failed: {str(e)}"],
        }

    # -------------------------
    # NEW (2): One-page summary (executive)
    # -------------------------
    one_page_summary = {}
    try:
        llm = LLMClient()
        one_page_summary = generate_one_page_summary(
            llm_client=llm,
            ticker=ticker,
            as_of=asof,
            company_profile=profile,
            metrics=metrics,
            rag_sections={
                "quarter_highlights": {"bullets": sec1.bullets, "citations": [c.model_dump() for c in sec1.citations]},
                "capex_signals": {"bullets": sec2.bullets, "citations": [c.model_dump() for c in sec2.citations]},
                "risks": {"bullets": sec3.bullets, "citations": [c.model_dump() for c in sec3.citations]},
                "segment_drivers": {"bullets": sec4.bullets, "citations": [c.model_dump() for c in sec4.citations]},
                "business": biz_swot.get("business", {}),
                "swot": biz_swot.get("swot", {}),
                "capex_financing": capex_financing,
                "news": news_block,
            },
        )
    except Exception as e:
        one_page_summary = {
            "as_of": asof,
            "bullets": [{"label": "Error", "text": f"one_page_summary_failed: {str(e)}", "citations": []}],
            "notes": "LLM generation failed",
        }

    # -------------------------
    # NEW: Provenance (for Sources section + PDF)
    # -------------------------
    try:
        chunk_ids = []
        for sec in [sec1, sec2, sec3, sec4]:
            for c in sec.citations:
                if c.chunk_id:
                    chunk_ids.append(c.chunk_id)
        provenance = {
            "sec_urls": [filing["url"]] if filing.get("url") else [],
            "chunk_ids": sorted(set(chunk_ids))[:25],  # cap for PDF + UI
            "form": filing.get("form"),
            "filing_date": filing.get("filing_date"),
        }
    except Exception:
        provenance = {"sec_urls": [filing.get("url")] if filing.get("url") else [], "chunk_ids": []}
    


    payload = {
        "asof": asof,
        "company": profile,
        "metrics": metrics,
        "filing": {
            "form": filing["form"],
            "filing_date": filing["filing_date"],
            "source_url": filing["url"],
        },
        "sections": [sec1.model_dump(), sec2.model_dump(), sec3.model_dump(), sec4.model_dump()],
        "section_quality": quality,
        "business": biz_swot["business"],
        "swot": biz_swot["swot"],
        "news": news_block,
        "_errors": errors,
        "one_page_summary": one_page_summary,
        # NEW keys (UI + PDF)
        "capex_financing": capex_financing or None,
        "one_page_summary": one_page_summary or None,
        "provenance": provenance or None,
    }

    save_cache(cache_key, payload)
    return {"ticker": ticker, **payload}


# -------------------------
# Chunk lookup (keep)
# -------------------------
@app.get("/filings/chunk")
def filing_chunk(ticker: str, form: str, filing_date: str, chunk_id: str):
    ticker = ticker.upper()
    ch = get_chunk_by_id(ticker, form, filing_date, chunk_id)
    if not ch:
        return {
            "found": False,
            "message": "Chunk not found. If this is the first run, call /filings/summary_vector?reindex=true to create meta.",
        }
    return {
        "found": True,
        "ticker": ticker,
        "form": form,
        "filing_date": filing_date,
        "chunk_id": chunk_id,
        "section": ch.get("section"),
        "text": ch.get("text", "")[:12000],
    }


# -------------------------
# PDF export (keep)
# -------------------------
@app.get("/equity_report.pdf")
def equity_report_pdf(ticker: str, refresh: bool = False, reindex: bool = False):
    report = equity_report(ticker=ticker, refresh=refresh, reindex=reindex)
    pdf_bytes = build_equity_pdf(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{ticker.upper()}_report.pdf"'},
    )


# -------------------------
# News endpoints (fix summary)
# -------------------------
@app.get("/news")
def news(ticker: str, days: int = 7, limit: int = 30, refresh: bool = False):
    ticker = ticker.upper()
    asof = date.today().isoformat()

    cache_key = make_key("news", ticker, asof=asof)
    if not refresh:
        cached = load_cache(cache_key, ttl_seconds=60 * 30)
        if cached:
            return {"cached": True, "asof": asof, "ticker": ticker, "articles": cached["articles"]}

    articles = get_stock_news(ticker, days=days, limit=limit)
    payload = {"asof": asof, "ticker": ticker, "articles": articles}
    save_cache(cache_key, payload)
    return {"cached": False, **payload}


@app.get("/news/summary")
def news_summary(ticker: str, days: int = 7, limit: int = 25, refresh: bool = False):
    ticker = ticker.upper()
    asof = date.today().isoformat()

    cache_key = make_key("news_summary", ticker, asof=asof)
    if not refresh:
        cached = load_cache(cache_key, ttl_seconds=60 * 60)
        if cached:
            return {"cached": True, **cached}

    articles = get_stock_news(ticker, days=days, limit=limit)

    # compact context
    lines = []
    for i, a in enumerate(articles[:12], start=1):
        lines.append(
            f"[{i}] {a.get('publishedDate','')} | {a.get('site','')} | {a.get('title','')}\n"
            f"URL: {a.get('url','')}\n"
            f"Snippet: { (a.get('text') or '')[:350] }\n"
        )
    context = "\n".join(lines) if lines else "No articles found."

    system = (
        "You are a buy-side analyst. Summarize ONLY from the provided news items. "
        "Be factual. If unclear, say so. Output ONLY valid JSON."
    )
    user = f"""
Ticker: {ticker}
Window: last {days} days

News items:
{context}

Output JSON with keys:
- top_themes: 3-6 bullets
- catalysts: 3-6 bullets
- risks: 3-6 bullets
- notable_articles: list of {{"id": number, "title": "...", "why_it_matters": "..."}}
"""

    llm = LLMClient()
    raw = llm.summarize(system, user)

    try:
        summary_json = json.loads(raw)
    except Exception:
        # graceful fallback
        summary_json = {
            "top_themes": ["LLM returned non-JSON output"],
            "catalysts": [],
            "risks": [],
            "notable_articles": [],
            "_raw": raw[:2000],
        }

    payload = {
        "ticker": ticker,
        "asof": asof,
        "days": days,
        "summary": summary_json,
        "citations": [
            {"id": i + 1, "url": a.get("url"), "title": a.get("title"), "publishedDate": a.get("publishedDate")}
            for i, a in enumerate(articles[:12])
        ],
    }
    save_cache(cache_key, payload)
    return {"cached": False, **payload}