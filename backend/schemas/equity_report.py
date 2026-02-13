from __future__ import annotations

from pydantic import BaseModel,Field
from typing import Any, Dict, List, Optional

class Citation(BaseModel):
    chunk_id: str
    section: str
    source_url: str
    score: Optional[float] = None

class ReportSection(BaseModel):
    title: str
    bullets: List[str]
    citations: List[Citation] = []

class SWOTBlock(BaseModel):
    bullets: List[str] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)

class BusinessBlock(BaseModel):

    bullets: List[str] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)


class BusinessSection(BaseModel):
    segments: BusinessBlock = BusinessBlock()
    revenue_characteristics: BusinessBlock = BusinessBlock()
    geographies: BusinessBlock = BusinessBlock()
    kpis: BusinessBlock = BusinessBlock()

class SWOTSection(BaseModel):
    strengths: SWOTBlock = SWOTBlock()
    weaknesses: SWOTBlock = SWOTBlock()
    opportunities: SWOTBlock = SWOTBlock()
    threats: SWOTBlock = SWOTBlock()


# -------------------------
# NEW: One-page summary schema
# -------------------------

class SummaryCitation(BaseModel):
    chunk_id: str
    doc_type: Optional[str] = None
    filing_date: Optional[str] = None
    url: Optional[str] = None

class OnePagerBullet(BaseModel):
    label: str
    text: str
    citations: List[SummaryCitation] = []

class OnePageSummary(BaseModel):
    as_of: str
    bullets: List[OnePagerBullet] = []
    notes: Optional[str] = None
    _meta: Optional[Dict[str, Any]] = None


# -------------------------
# NEW: CAPEX & Financing schema
# -------------------------

class CapexFinCitation(BaseModel):
    chunk_id: str
    doc_type: Optional[str] = None
    filing_date: Optional[str] = None
    url: Optional[str] = None

class CapexFinBullet(BaseModel):
    label: str
    text: str
    citations: List[CapexFinCitation] = []

class CapexFinancingSection(BaseModel):
    capex_investment_bullets: List[CapexFinBullet] = []
    financing_and_capital_allocation: List[CapexFinBullet] = []
    missing: List[str] = []
    _meta: Optional[Dict[str, Any]] = None

class Provenance(BaseModel):
    sec_urls: List[str] = []
    chunk_ids: List[str] = []
    # optionally store filing info you already show in UI
    form: Optional[str] = None
    filing_date: Optional[str] = None


class EquityReport(BaseModel):
    ticker: str
    asof: str
    company: Dict[str, Any]
    metrics: Dict[str, Any]
    filing: Dict[str, Any]
    sections: List[ReportSection]
    section_quality: Optional[Dict[str, Dict[str, float]]] = None
    news: Optional[Dict[str, Any]] = None
    business: Optional[BusinessSection] = None
    swot: Optional[SWOTSection] = None

    # NEW fields
    one_page_summary: Optional[OnePageSummary] = None
    capex_financing: Optional[CapexFinancingSection] = None
    provenance: Optional[Provenance] = None

EquityReport.model_rebuild()