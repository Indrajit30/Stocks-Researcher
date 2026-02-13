# backend/services/sec_client.py
from __future__ import annotations
import requests
from typing import Any, Dict, Optional

class SECError(Exception):
    pass

class SECClient:
    """
    Uses SEC data APIs on data.sec.gov.
    SEC expects a descriptive User-Agent identifying your app + contact.
    """
    BASE_DATA = "https://data.sec.gov"
    TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"

    def __init__(self, user_agent: str, timeout: int = 30):
        if not user_agent or "@" not in user_agent:
            # not strictly required, but strongly recommended for fair access
            raise SECError("Set a descriptive SEC User-Agent like: 'StockIntel (your_email@domain.com)'")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
        self.timeout = timeout

    def get_json(self, url: str) -> Any:
        r = self.session.get(url, timeout=self.timeout)
        if not r.ok:
            raise SECError(f"HTTP {r.status_code} from SEC: {r.text[:200]}")
        return r.json()

    def ticker_to_cik(self, ticker: str) -> str:
        data = self.get_json(self.TICKER_MAP_URL)  # dict keyed by ints
        t = ticker.upper()
        for _, row in data.items():
            if row.get("ticker", "").upper() == t:
                cik_int = int(row["cik_str"])
                return str(cik_int).zfill(10)  # SEC submissions use zero-padded CIK
        raise SECError(f"CIK not found for ticker={ticker}")

    def company_submissions(self, cik_padded_10: str) -> Dict[str, Any]:
        url = f"{self.BASE_DATA}/submissions/CIK{cik_padded_10}.json"
        return self.get_json(url)

    def latest_filing(self, ticker: str, form_type: str = "10-Q") -> Dict[str, Any]:
        cik = self.ticker_to_cik(ticker)
        sub = self.company_submissions(cik)

        recent = sub.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession = recent.get("accessionNumber", [])
        primary_doc = recent.get("primaryDocument", [])
        filing_date = recent.get("filingDate", [])

        for i, f in enumerate(forms):
            if f == form_type:
                return {
                    "cik": cik,
                    "form": f,
                    "filing_date": filing_date[i],
                    "accession_number": accession[i],
                    "primary_document": primary_doc[i],
                }

        raise SECError(f"No {form_type} found for {ticker}")
