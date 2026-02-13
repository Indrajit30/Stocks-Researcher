from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional, Callable

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


FONT_BODY = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def _fmt_pct(v: Optional[float]) -> Optional[str]:
    if v is None:
        return None
    return f"{v * 100:.1f}%"


def _fmt_num(v: Optional[float]) -> Optional[str]:
    if v is None:
        return None
    try:
        return f"{v:,.2f}"
    except Exception:
        return str(v)


def _strip_md(s: str) -> str:
    if not s:
        return s
    return (
        s.replace("**", "")
        .replace("`", "")
        .replace("•", "")
        .strip()
    )


def _get_block_bullets(block: Any) -> List[str]:
    """
    Supports:
    - {"bullets":[...]} shape
    - list[str]
    - str
    """
    if block is None:
        return []
    if isinstance(block, dict):
        b = block.get("bullets")
        if isinstance(b, list):
            return [_strip_md(str(x)) for x in b if x]
        if isinstance(b, str) and b.strip():
            return [_strip_md(b.strip())]
        return []
    if isinstance(block, list):
        return [_strip_md(str(x)) for x in block if x]
    if isinstance(block, str) and block.strip():
        return [_strip_md(block.strip())]
    return []


def draw_footer(c: canvas.Canvas, report: Dict[str, Any], page_width: float) -> None:
    ticker = report.get("ticker", "") or ""
    asof = report.get("asof", "") or ""
    c.setFont(FONT_BODY, 8)
    c.drawString(0.65 * inch, 0.45 * inch, f"{ticker} • {asof}")
    c.drawRightString(page_width - 0.65 * inch, 0.45 * inch, f"Page {c.getPageNumber()}")


def draw_page_frame(c: canvas.Canvas, report: Dict[str, Any], width: float, height: float) -> float:
    """
    Draws header + rule (full width) on the current page.
    Returns y coordinate where 2-column content should begin.
    """
    company = report.get("company", {}) or {}
    ticker = report.get("ticker", "") or ""
    name = company.get("name") or company.get("companyName") or ticker

    header_x = 0.65 * inch
    header_y = height - 0.85 * inch

    c.setFont(FONT_BOLD, 16)
    c.drawString(header_x, header_y, f"{name} ({ticker})".strip())

    asof = report.get("asof")
    sector = company.get("sector")
    industry = company.get("industry")

    c.setFont(FONT_BODY, 10)
    if asof:
        c.drawString(header_x, header_y - 16, f"As of: {asof}")

    desc = " • ".join([x for x in [sector, industry] if x])
    if desc:
        c.setFont(FONT_BODY, 9.5)
        c.drawString(header_x, header_y - 30, desc)

    rule_y = header_y - 42
    c.setLineWidth(0.7)
    c.line(header_x, rule_y, width - header_x, rule_y)

    draw_footer(c, report, width)
    return rule_y - 18


def draw_continuation_frame(c: canvas.Canvas, report: Dict[str, Any], width: float, height: float) -> float:
    """
    Frame for pages 2+:
    - NO main header/title
    - Optional thin rule
    - Footer only
    Returns y coordinate where content should begin.
    """
    x = 0.65 * inch
    top_y = height - 0.85 * inch

    # optional: a subtle rule (comment out if you want nothing)
    c.setLineWidth(0.7)
    c.line(x, top_y, width - x, top_y)

    draw_footer(c, report, width)
    return top_y - 18


def _draw_fullwidth_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    maxw: float,
    lh: float,
    font: str = FONT_BODY,
    size: float = 9.0,
) -> float:
    """
    Full width wrapper that also breaks long tokens (URLs).
    """
    text = _strip_md(text or "")
    if not text:
        return y

    c.setFont(font, size)

    def split_long(token: str) -> List[str]:
        chunks: List[str] = []
        cur = ""
        for ch in token:
            test = cur + ch
            if c.stringWidth(test, font, size) <= maxw:
                cur = test
            else:
                if cur:
                    chunks.append(cur)
                cur = ch
        if cur:
            chunks.append(cur)
        return chunks

    words = text.split()
    expanded: List[str] = []
    for w in words:
        if c.stringWidth(w, font, size) <= maxw:
            expanded.append(w)
        else:
            expanded.extend(split_long(w))

    line = ""
    for w in expanded:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font, size) <= maxw:
            line = test
        else:
            if line:
                c.drawString(x, y, line)
                y -= lh
            line = w

    if line:
        c.drawString(x, y, line)
        y -= lh

    return y - 6


class TwoColFlow:
    def __init__(
        self,
        c: canvas.Canvas,
        page_width: float,
        page_height: float,
        margin_x: float = 0.65 * inch,
        margin_bottom: float = 0.65 * inch,
        gutter: float = 0.38 * inch,
        first_page_frame_fn: Optional[Callable[[], float]] = None,
        other_pages_frame_fn: Optional[Callable[[], float]] = None,
    ):
        self.c = c
        self.w = page_width
        self.h = page_height
        self.margin_x = margin_x
        self.margin_bottom = margin_bottom
        self.gutter = gutter
        self.first_page_frame_fn = first_page_frame_fn
        self.other_pages_frame_fn = other_pages_frame_fn

        usable_w = self.w - 2 * self.margin_x
        self.col_w = (usable_w - self.gutter) / 2.0
        self.col_x = [self.margin_x, self.margin_x + self.col_w + self.gutter]

        self.col = 0

        # Page 1: draw big header once
        if self.first_page_frame_fn:
            self.page_top_y = self.first_page_frame_fn()
        else:
            self.page_top_y = self.h - 1.75 * inch

        self.y = self.page_top_y
        self.c.setFont(FONT_BODY, 9.5)

    def _new_page(self):
        self.c.showPage()
        self.c.setFont(FONT_BODY, 9.5)
        self.col = 0

        # Pages 2+: draw continuation frame (NO big header)
        if self.other_pages_frame_fn:
            self.page_top_y = self.other_pages_frame_fn()
        elif self.first_page_frame_fn:
            # fallback: if only one fn provided, use it
            self.page_top_y = self.first_page_frame_fn()
        else:
            self.page_top_y = self.h - 1.75 * inch

        self.y = self.page_top_y

    def _next_col_or_page(self):
        if self.col == 0:
            self.col = 1
            self.y = self.page_top_y
        else:
            self._new_page()

    def ensure(self, needed: float):
        if self.y - needed < self.margin_bottom:
            self._next_col_or_page()

    def reserve(self, min_height: float):
        """
        Ensures at least min_height is available in current column,
        else moves to next column/page BEFORE drawing the section.
        """
        if self.y - min_height < self.margin_bottom:
            self._next_col_or_page()

    def _split_long_token(self, token: str, font: str, size: float, max_width: float) -> List[str]:
        chunks: List[str] = []
        cur = ""
        for ch in token:
            test = cur + ch
            if self.c.stringWidth(test, font, size) <= max_width:
                cur = test
            else:
                if cur:
                    chunks.append(cur)
                cur = ch
        if cur:
            chunks.append(cur)
        return chunks

    # -------------------------
    # NEW: pre-wrap helper for hanging bullets
    # -------------------------
    def _wrap_hanging_lines(
        self,
        text: str,
        font: str,
        size: float,
        max_width: float,
    ) -> List[str]:
        """
        Wrap text to fit max_width, splitting long tokens if needed.
        Returns a list of wrapped lines (no bullet char, no indentation).
        """
        text = _strip_md(text or "")
        if not text:
            return []

        self.c.setFont(font, size)

        words = text.split()
        expanded: List[str] = []
        for w in words:
            if self.c.stringWidth(w, font, size) <= max_width:
                expanded.append(w)
            else:
                expanded.extend(self._split_long_token(w, font, size, max_width))

        lines: List[str] = []
        line = ""
        for w in expanded:
            test = (line + " " + w).strip()
            if self.c.stringWidth(test, font, size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w

        if line:
            lines.append(line)

        return lines

    def heading(self, title: str):
        self.ensure(16)
        self.c.setFont(FONT_BOLD, 10.8)
        self.c.drawString(self.col_x[self.col], self.y, title)
        self.y -= 13
        self.c.setFont(FONT_BODY, 9.5)

    def subheading(self, title: str):
        self.ensure(14)
        self.c.setFont(FONT_BOLD, 9.9)
        self.c.drawString(self.col_x[self.col], self.y, title)
        self.y -= 12
        self.c.setFont(FONT_BODY, 9.5)

    def wrapped(self, text: str, font: str = FONT_BODY, size: float = 9.5, lh: float = 11) -> None:
        text = _strip_md(text or "")
        if not text:
            return

        self.c.setFont(font, size)
        x = self.col_x[self.col]
        maxw = self.col_w

        words = text.split()
        expanded: List[str] = []
        for w in words:
            if self.c.stringWidth(w, font, size) <= maxw:
                expanded.append(w)
            else:
                expanded.extend(self._split_long_token(w, font, size, maxw))

        line = ""
        for w in expanded:
            test = (line + " " + w).strip()
            if self.c.stringWidth(test, font, size) <= maxw:
                line = test
            else:
                if line:
                    self.ensure(lh)
                    self.c.drawString(x, self.y, line)
                    self.y -= lh
                line = w

        if line:
            self.ensure(lh)
            self.c.drawString(x, self.y, line)
            self.y -= lh

        self.c.setFont(FONT_BODY, 9.5)

    # -------------------------
    # CHANGED: bullet_hanging now reserves whole bullet BEFORE drawing
    # -------------------------
    def bullet_hanging(self, text: str, size: float = 9.5, lh: float = 11):
        text = _strip_md(text or "")
        if not text:
            return

        bullet = "•"
        x0 = self.col_x[self.col]
        maxw = self.col_w
        indent = 10  # points
        font = FONT_BODY

        # Wrap first (using width after indent)
        lines = self._wrap_hanging_lines(
            text=text,
            font=font,
            size=size,
            max_width=(maxw - indent),
        )
        if not lines:
            return

        # Reserve space for entire bullet to avoid mid-bullet column/page breaks
        needed = len(lines) * lh
        if self.y - needed < self.margin_bottom:
            self._next_col_or_page()
            x0 = self.col_x[self.col]

        self.c.setFont(font, size)

        first = True
        for line in lines:
            # Safety: if extremely long bullet still can't fit (rare)
            if self.y - lh < self.margin_bottom:
                self._next_col_or_page()
                x0 = self.col_x[self.col]
                self.c.setFont(font, size)
                first = False  # don't redraw the bullet dot again

            if first:
                self.c.drawString(x0, self.y, bullet)
                self.c.drawString(x0 + indent, self.y, line)
                first = False
            else:
                self.c.drawString(x0 + indent, self.y, line)

            self.y -= lh

        self.c.setFont(FONT_BODY, 9.5)

    def bullet_list(self, bullets: List[str], max_items: int = 6):
        for b in (bullets or [])[:max_items]:
            if b:
                self.bullet_hanging(b, size=9.5, lh=11)
        self.y -= 5

    def kv_table(self, rows: List[List[str]]):
        if not rows:
            return
        x = self.col_x[self.col]
        maxw = self.col_w
        label_w = maxw * 0.62
        val_w = maxw - label_w

        self.c.setFont(FONT_BODY, 9.5)
        for label, val in rows:
            label = _strip_md(label or "")
            val = _strip_md(val or "")
            if not label or not val:
                continue

            self.ensure(12)
            self.c.drawString(x, self.y, label[:90])
            self.c.drawRightString(x + label_w + val_w, self.y, val[:40])
            self.y -= 11

        self.y -= 6


def build_equity_pdf(report: Dict[str, Any], include_sources: bool = False) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    width, height = LETTER

    flow = TwoColFlow(
        c,
        width,
        height,
        first_page_frame_fn=lambda: draw_page_frame(c, report, width, height),
        other_pages_frame_fn=lambda: draw_continuation_frame(c, report, width, height),
    )

    # -------------------------
    # One-page Summary (CAP 8)
    # -------------------------
    ops = report.get("one_page_summary") or {}
    ops_bullets: List[str] = []
    if isinstance(ops, dict) and isinstance(ops.get("bullets"), list):
        for item in ops["bullets"][:8]:
            if not isinstance(item, dict):
                continue
            label = _strip_md((item.get("label") or "").strip())
            text = _strip_md((item.get("text") or "").strip())
            if text:
                ops_bullets.append(f"[{label}] {text}" if label else text)

    if ops_bullets:
        flow.reserve(70)
        flow.heading("One-page Summary")
        flow.bullet_list(ops_bullets, max_items=8)

    # -------------------------
    # Key Metrics (compact table)
    # -------------------------
    metrics = report.get("metrics", {}) or {}
    rows: List[List[str]] = []

    cagr = metrics.get("revenue_cagr")
    cagr_years = metrics.get("revenue_cagr_years")
    opm = metrics.get("operating_margin")
    nd = metrics.get("net_debt_to_ebitda")

    if cagr is not None:
        yrs = f"{cagr_years}Y" if cagr_years else ""
        rows.append([f"Revenue CAGR {yrs}".strip(), _fmt_pct(float(cagr)) or ""])
    if opm is not None:
        rows.append(["Operating Margin", _fmt_pct(float(opm)) or ""])
    if nd is not None:
        rows.append(["Net Debt / EBITDA", _fmt_num(float(nd)) or ""])

    if rows:
        flow.reserve(55)
        flow.heading("Key Metrics")
        flow.kv_table(rows)

    # -------------------------
    # Latest Filing Used
    # -------------------------
    filing = report.get("filing", {}) or {}
    form = filing.get("form")
    filing_date = filing.get("filing_date")
    source_url = filing.get("source_url") or filing.get("url")

    if form or filing_date or source_url:
        flow.reserve(55)
        flow.heading("Latest Filing Used")
        top = " | ".join([x for x in [form, filing_date] if x])
        if top:
            flow.wrapped(top, font=FONT_BODY, size=9.5, lh=11)
        if source_url:
            flow.wrapped(f"Source: {source_url}", font=FONT_BODY, size=8.2, lh=9.6)
        flow.y -= 6

    # -------------------------
    # Highlights (CAP each section bullets to 3)
    # -------------------------
    sections: List[Dict[str, Any]] = report.get("sections", []) or []
    if sections:
        flow.reserve(85)
        flow.heading("Highlights")
        for sec in sections[:5]:
            title = _strip_md((sec.get("title") or "").strip())
            bullets = [_strip_md(str(b)) for b in (sec.get("bullets") or []) if b]
            if not title or not bullets:
                continue

            flow.reserve(45)
            flow.subheading(title)
            flow.bullet_list(bullets, max_items=3)

    # -------------------------
    # Business (CAP 2 each)
    # -------------------------
    biz = report.get("business") or {}
    if isinstance(biz, dict):
        segs = _get_block_bullets(biz.get("segments"))
        rev = _get_block_bullets(biz.get("revenue_characteristics"))
        geos = _get_block_bullets(biz.get("geographies"))
        kpis = _get_block_bullets(biz.get("kpis"))

        if any([segs, rev, geos, kpis]):
            flow.reserve(95)
            flow.heading("Understanding the Business")

            if segs:
                flow.reserve(40)
                flow.subheading("Segments")
                flow.bullet_list(segs, max_items=2)

            if rev:
                flow.reserve(35)
                flow.subheading("Revenue characteristics")
                flow.bullet_list(rev, max_items=2)

            if geos:
                flow.reserve(35)
                flow.subheading("Geography")
                flow.bullet_list(geos, max_items=2)

            if kpis:
                flow.reserve(35)
                flow.subheading("KPIs")
                flow.bullet_list(kpis, max_items=2)

    # -------------------------
    # SWOT (CAP 2 each)
    # -------------------------
    swot = report.get("swot") or {}
    if isinstance(swot, dict):
        strengths = _get_block_bullets(swot.get("strengths"))
        weaknesses = _get_block_bullets(swot.get("weaknesses"))
        opps = _get_block_bullets(swot.get("opportunities"))
        threats = _get_block_bullets(swot.get("threats"))

        if any([strengths, weaknesses, opps, threats]):
            flow.reserve(95)
            flow.heading("SWOT")

            if strengths:
                flow.reserve(35)
                flow.subheading("Strengths")
                flow.bullet_list(strengths, max_items=2)

            if weaknesses:
                flow.reserve(35)
                flow.subheading("Weaknesses")
                flow.bullet_list(weaknesses, max_items=2)

            if opps:
                flow.reserve(35)
                flow.subheading("Opportunities")
                flow.bullet_list(opps, max_items=2)

            if threats:
                flow.reserve(35)
                flow.subheading("Threats")
                flow.bullet_list(threats, max_items=2)

    # -------------------------
    # Sources (REMOVED by default)
    # -------------------------
    if include_sources:
        prov = report.get("provenance") or {}
        if isinstance(prov, dict):
            sec_urls = prov.get("sec_urls") or []
            chunk_ids = prov.get("chunk_ids") or []
            if sec_urls or chunk_ids:
                c.showPage()
                draw_footer(c, report, width)

                x = 0.65 * inch
                y = height - 0.85 * inch
                maxw = width - 2 * x

                c.setFont(FONT_BOLD, 14)
                c.drawString(x, y, "Sources")
                y -= 18

                if sec_urls:
                    y = _draw_fullwidth_wrapped(
                        c,
                        f"SEC: {sec_urls[0]}",
                        x,
                        y,
                        maxw,
                        12,
                        font=FONT_BODY,
                        size=9,
                    )

                if chunk_ids:
                    ids = ", ".join([str(cid) for cid in chunk_ids[:25]])
                    y = _draw_fullwidth_wrapped(
                        c,
                        f"Chunk IDs: {ids}",
                        x,
                        y,
                        maxw,
                        12,
                        font=FONT_BODY,
                        size=9,
                    )

    c.save()
    return buf.getvalue()
