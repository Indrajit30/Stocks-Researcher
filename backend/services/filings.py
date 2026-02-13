# backend/services/filings.py
from __future__ import annotations
from typing import Dict
import os
import requests

from backend.services.sec_client import SECClient, SECError

def _accession_no_dashes(accession: str) -> str:
    return accession.replace("-", "")

def get_latest_filing_html(ticker: str, form_type: str = "10-Q") -> Dict[str, str]:
    """
    Returns: metadata + raw HTML text for the latest filing primary document.
    """
    ua = os.getenv("SEC_USER_AGENT", "StockIntel (your_email@example.com)")
    sec = SECClient(user_agent=ua)

    meta = sec.latest_filing(ticker, form_type=form_type)
    cik = meta["cik"]
    accession = meta["accession_number"]
    doc = meta["primary_document"]

    # Filing document URL pattern:
    # https://www.sec.gov/Archives/edgar/data/{cik_int}/{accessionNoDashes}/{primaryDocument}
    cik_int = str(int(cik))  # remove leading zeros for the archive path
    acc_nodash = _accession_no_dashes(accession)
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{doc}"

    r = requests.get(url, headers={"User-Agent": ua}, timeout=30)
    if not r.ok:
        raise SECError(f"Could not download filing HTML: HTTP {r.status_code}")

    return {
        "url": url,
        "filing_date": meta["filing_date"],
        "form": meta["form"],
        "accession_number": accession,
        "html": r.text,
    }
