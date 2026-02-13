# backend/services/providers.py
from __future__ import annotations
from typing import Any, Dict, List
from backend.services.fmp_client import FMPClient, FMPError

client = FMPClient()

def _pick_first_row(data: Any) -> Dict[str, Any]:
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        return data[0]
    return {}

def get_company_profile(ticker: str) -> Dict[str, Any]:
    # https://financialmodelingprep.com/stable/profile?symbol=AAPL
    data = client.get("profile", params={"symbol": ticker.upper()})
    row = _pick_first_row(data)
    # keep fields you care about; you can expand later
    return {
        "ticker": ticker.upper(),
        "name": row.get("companyName") or row.get("name") or ticker.upper(),
        "sector": row.get("sector"),
        "industry": row.get("industry"),
        "country": row.get("country"),
        "exchange": row.get("exchangeShortName") or row.get("exchange"),
        "website": row.get("website"),
        "description": row.get("description"),
        "market_cap": row.get("mktCap") or row.get("marketCap"),
    }

def get_financial_snapshot(ticker: str) -> Dict[str, Any]:
    """
    Pull annual statements and compute a unified snapshot.
    We return:
    - revenue_series: [{year, value}] for CAGR
    - latest: revenue, operating_income, ebitda, total_debt, cash_and_equiv
    """
    sym = ticker.upper()

    # Endpoints:
    # /stable/income-statement?symbol=AAPL
    # /stable/balance-sheet-statement?symbol=AAPL
    # /stable/cash-flow-statement?symbol=AAPL
    income = client.get("income-statement", params={"symbol": sym})
    balance = client.get("balance-sheet-statement", params={"symbol": sym})
    cashflow = client.get("cash-flow-statement", params={"symbol": sym})

    if not isinstance(income, list) or len(income) == 0:
        raise FMPError(f"No income statement data for {sym}")

    # revenue series (annual)
    revenue_series: List[Dict[str, Any]] = []
    for row in income:
        # FMP often returns "calendarYear" and numeric fields like "revenue"
        year = row.get("calendarYear") or row.get("date", "")[:4]
        rev = row.get("revenue")
        if year and rev is not None:
            try:
                revenue_series.append({"year": int(year), "value": float(rev)})
            except Exception:
                pass

    latest_income = income[0]  # most recent first (commonly)
    latest_balance = balance[0] if isinstance(balance, list) and balance else {}
    latest_cashflow = cashflow[0] if isinstance(cashflow, list) and cashflow else {}

    # operating income & EBITDA
    operating_income = latest_income.get("operatingIncome")
    ebitda = latest_income.get("ebitda") or latest_cashflow.get("ebitda")

    # debt + cash
    # debt field names vary; we try common ones
    total_debt = (
        latest_balance.get("totalDebt")
        or latest_balance.get("shortTermDebt")  # fallback if totalDebt not present
    )
    cash_and_equiv = (
        latest_balance.get("cashAndCashEquivalents")
        or latest_balance.get("cashAndShortTermInvestments")  # sometimes easier to get
    )

    return {
        "revenue_series": revenue_series,
        "latest": {
            "revenue": float(latest_income.get("revenue")) if latest_income.get("revenue") is not None else None,
            "operating_income": float(operating_income) if operating_income is not None else None,
            "ebitda": float(ebitda) if ebitda is not None else None,
            "total_debt": float(total_debt) if total_debt is not None else None,
            "cash_and_equiv": float(cash_and_equiv) if cash_and_equiv is not None else None,
        }
    }
