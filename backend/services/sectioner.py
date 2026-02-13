# backend/services/sectioner.py
from __future__ import annotations
import re
from typing import Dict, List, Tuple

# Flexible patterns for SEC filings
SECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("item_1", re.compile(r"^\s*item\s+1[\.\:]\s*", re.IGNORECASE)),
    ("item_1a", re.compile(r"^\s*item\s+1a[\.\:]\s*", re.IGNORECASE)),
    ("item_2", re.compile(r"^\s*item\s+2[\.\:]\s*", re.IGNORECASE)),
    ("item_3", re.compile(r"^\s*item\s+3[\.\:]\s*", re.IGNORECASE)),
    ("item_4", re.compile(r"^\s*item\s+4[\.\:]\s*", re.IGNORECASE)),
    ("risk_factors", re.compile(r"^\s*risk\s+factors\s*$", re.IGNORECASE)),
    ("mda", re.compile(r"^\s*management[’']s\s+discussion\s+and\s+analysis", re.IGNORECASE)),
]

def split_into_sections(text: str) -> Dict[str, str]:
    """
    Best-effort sectioning by scanning lines and starting a new section
    when a heading-like line matches a known pattern.
    """
    lines = text.splitlines()
    section_order: List[str] = ["preamble"]
    buckets: Dict[str, List[str]] = {"preamble": []}

    current = "preamble"
    for line in lines:
        # treat "short" lines as possible headings
        is_heading_candidate = len(line) <= 120

        if is_heading_candidate:
            for name, pat in SECTION_PATTERNS:
                if pat.search(line):
                    current = name
                    if current not in buckets:
                        buckets[current] = []
                        section_order.append(current)
                    # keep the heading line
                    buckets[current].append(line)
                    break
            else:
                buckets[current].append(line)
        else:
            buckets[current].append(line)

    return {k: "\n".join(buckets[k]).strip() for k in section_order if buckets.get(k)}
