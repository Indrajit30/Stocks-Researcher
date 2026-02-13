# backend/services/fmp_client.py
from __future__ import annotations
import os
import requests
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class FMPError(Exception):
    pass

class FMPClient:
    """
    Minimal FMP client for the 'stable' endpoints.
    Base URL and apikey pattern per FMP quickstart.
    """
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise FMPError("Missing FMP_API_KEY. Put it in .env or environment.")
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = dict(params or {})
        params["apikey"] = self.api_key

        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        r = self.session.get(url, params=params, timeout=self.timeout)

        # basic error handling
        if r.status_code == 401 or r.status_code == 403:
            raise FMPError(f"Auth error ({r.status_code}). Check API key/plan.")
        if r.status_code == 429:
            raise FMPError("Rate limited (429). Add TTL caching or backoff.")
        if not r.ok:
            raise FMPError(f"HTTP {r.status_code}: {r.text[:200]}")

        try:
            return r.json()
        except Exception as e:
            raise FMPError(f"Invalid JSON: {e}") from e
