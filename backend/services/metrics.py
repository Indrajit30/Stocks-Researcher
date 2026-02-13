# backend/services/metrics.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

@dataclass
class SeriesPoint:
    year: int
    value: float

def revenue_cagr(series: List[SeriesPoint], max_years: int = 10) -> Optional[Tuple[float, int]]:
    """
    Computes Revenue CAGR using up to `max_years` of available data.

    Returns:
        (cagr_decimal, years_used)
        e.g. (0.12, 8)  -> 12% CAGR over 8 years

    Returns None if fewer than 2 valid points exist.
    """
    if not series or len(series) < 2:
        return None

    # sort by year
    s = sorted(series, key=lambda x: x.year)

    # usable years = min(max_years, available span)
    years_available = len(s) - 1
    years_used = min(max_years, years_available)

    start = s[-(years_used + 1)].value
    end = s[-1].value

    if start <= 0 or end <= 0:
        return None

    cagr = (end / start) ** (1.0 / years_used) - 1.0
    return cagr, years_used

def operating_margin(operating_income: float, revenue: float) -> Optional[float]:
    if revenue == 0:
        return None
    return operating_income / revenue

def net_debt_to_ebitda(total_debt: float, cash_and_equiv: float, ebitda: float) -> Optional[float]:
    if ebitda == 0:
        return None
    net_debt = total_debt - cash_and_equiv
    return net_debt / ebitda