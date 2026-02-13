# backend/services/html_to_text.py
from __future__ import annotations

import re
from bs4 import BeautifulSoup

WHITESPACE_RE = re.compile(r"[ \t]+")
NEWLINES_RE = re.compile(r"\n{3,}")

def html_to_clean_text(html: str) -> str:
    """
    Convert SEC filing HTML to clean plain text.

    Notes:
    - Removes scripts/styles
    - Drops inline XBRL hidden blocks automatically (most are display:none)
    - Produces readable text with normalized whitespace
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove junk nodes
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Remove elements that are explicitly hidden (common in Inline XBRL)
    for tag in soup.select('[style*="display:none"]'):
        tag.decompose()

    # Get text with line breaks
    text = soup.get_text("\n")

    # Normalize whitespace
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = WHITESPACE_RE.sub(" ", line)
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = NEWLINES_RE.sub("\n\n", cleaned)
    return cleaned.strip()
