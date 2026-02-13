// API Client for Stock Intelligence Backend

// export const API_BASE = "http://127.0.0.1:8000";
export const API_BASE = "https://venessa-nonpreventable-tanisha.ngrok-free.dev";

// Types for the API responses
export interface Company {
  name: string;
  sector?: string;
  industry?: string;
  country?: string;
  market_cap?: number;
}

export interface Metrics {
  revenue_cagr?: number;
  revenue_cagr_years?: number;
  operating_margin?: number;
  net_debt_to_ebitda?: number;
}

export interface Filing {
  form?: string;
  filing_date?: string;
  source_url?: string;
}

export interface Citation {
  chunk_id: string;
  section?: string;
  source_url?: string;
  score?: number;
}

export interface Bullet {
  label?: string;
  text: string;
  citations?: Citation[];
}

export interface OnePageSummary {
  bullets: Bullet[];
  notes?: string;
}

export interface Section {
  title: string;
  bullets: string[];
  citations: Citation[];
}

export interface SectionQuality {
  coverage?: number;
  avg_score?: number;
}

export interface BusinessBlock {
  bullets: string[];
  citations?: Citation[];
}

export interface Business {
  segments?: BusinessBlock;
  revenue_characteristics?: BusinessBlock;
  geographies?: BusinessBlock;
  geography?: BusinessBlock;
  kpis?: BusinessBlock;
}

export interface SwotSection {
  bullets: string[];
  citations?: Citation[];
}

export interface Swot {
  strengths?: SwotSection;
  weaknesses?: SwotSection;
  opportunities?: SwotSection;
  threats?: SwotSection;
}

export interface NewsArticle {
  title: string;
  publishedDate?: string;
  site?: string;
  url?: string;
  text?: string;
}

export interface News {
  window_days?: number;
  articles: NewsArticle[];
}

export interface ApiError {
  step: string;
  error_type: string;
  message: string;
}

export interface CapexFinancing {
  capex_investment_bullets?: Bullet[];
  financing_and_capital_allocation?: Bullet[];
  missing?: string[];
}

export interface EquityReport {
  ticker: string;
  asof?: string;
  company: Company;
  metrics: Metrics;
  filing: Filing;
  one_page_summary?: OnePageSummary;
  sections: Section[];
  section_quality?: Record<string, SectionQuality>;
  business?: Business;
  swot?: Swot;
  news?: News;
  capex_financing?: CapexFinancing;
  _errors?: ApiError[];
  _timings_ms?: Record<string, number>;
}

export interface ChunkResponse {
  found: boolean;
  text?: string;
  section?: string;
  message?: string;
}

// API Functions
// export async function fetchEquityReport(
//   ticker: string,
//   refresh: boolean = false,
//   reindex: boolean = false
// ): Promise<EquityReport> {
//   const params = new URLSearchParams({
//     ticker: ticker.toUpperCase(),
//     refresh: refresh.toString(),
//     reindex: reindex.toString(),
//   });

//   const response = await fetch(`${API_BASE}/equity_report?${params}`, {
//     method: "GET",
//     headers: {
//       "Accept": "application/json",
//     },
//   });

//   if (!response.ok) {
//     const errorText = await response.text();
//     throw new Error(`Backend error ${response.status}: ${errorText}`);
//   }

//   return response.json();
// }
export async function fetchEquityReport(
  ticker: string,
  refresh: boolean = false,
  reindex: boolean = false
): Promise<EquityReport> {
  if (!ticker || !ticker.trim()) {
    throw new Error("Ticker is required (e.g., MSFT).");
  }

  const params = new URLSearchParams({
    ticker: ticker.trim().toUpperCase(),
    refresh: String(refresh),
    reindex: String(reindex),
  });

  const url = `${API_BASE.replace(/\/$/, "")}/equity_report?${params}`;
  console.log("fetchEquityReport:", url);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
      // IMPORTANT for ngrok: prevents HTML interstitial page
      "ngrok-skip-browser-warning": "true",
    },
  });

  const text = await response.text();

  if (!response.ok) {
    throw new Error(`Backend error ${response.status}: ${text.slice(0, 500)}`);
  }

  // If HTML slipped through, show a clear error
  if (text.trim().startsWith("<")) {
    throw new Error(
      `Expected JSON but got HTML from ${url}. First 120 chars: ${text
        .slice(0, 120)
        .replace(/\s+/g, " ")}`
    );
  }

  return JSON.parse(text) as EquityReport;
}


export async function fetchChunk(
  ticker: string,
  form: string,
  filingDate: string,
  chunkId: string
): Promise<ChunkResponse> {
  const params = new URLSearchParams({
    ticker: ticker.toUpperCase(),
    form,
    filing_date: filingDate,
    chunk_id: chunkId,
  });

  const response = await fetch(`${API_BASE}/filings/chunk?${params}`, {
    method: "GET",
    headers: {
      "Accept": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch chunk: ${response.status}`);
  }

  return response.json();
}

export function getPdfDownloadUrl(
  ticker: string,
  refresh: boolean = false,
  reindex: boolean = false
): string {
  const params = new URLSearchParams({
    ticker: ticker.toUpperCase(),
    refresh: refresh.toString(),
    reindex: reindex.toString(),
  });

  return `${API_BASE}/equity_report.pdf?${params}`;
}

// Utility functions
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
