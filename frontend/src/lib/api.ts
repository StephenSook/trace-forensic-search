/**
 * Trace API client.
 *
 * Mirrors the Pydantic schemas in `backend/schemas.py`. Field-name casing
 * is intentional and matches the backend exactly:
 *   - `SearchFilters` → snake_case (consumed by Vinh's filters.py)
 *   - `SearchResponse` envelope → snake_case (`total_matches`, `latency_ms`)
 *   - `SearchResult` / `MatchMapping` → camelCase (mirrors card props,
 *     so results render with zero transform)
 *   - `CasePayload` → snake_case (storage layer shape)
 */

// ── Base URL ──────────────────────────────────────────────────────────
//
// Vite injects `VITE_*` envs at build time. Fallback matches the
// backend port from PLAN.md (`uvicorn main:app --port 8000`).
const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

// ── Shared literal unions ─────────────────────────────────────────────

export type CaseType = "missing" | "unidentified";
export type Sex = "Male" | "Female";
export type SexFilter = Sex | "Unknown";
export type ConfidenceLabel = "HIGH CONFIDENCE" | "MEDIUM CONFIDENCE" | "LOW CONFIDENCE";

// ── Storage-layer payload (snake_case) ────────────────────────────────

export interface CasePayload {
  case_id: string;
  case_type: CaseType;
  sex: Sex;
  age_low: number;
  age_high: number;
  state: string;
  date_epoch: number;
  date_iso: string;
  physical_text: string;
  circumstances: string;
  clothing: string;
  image_url: string | null;
}

// ── /search request ───────────────────────────────────────────────────

export interface SearchFilters {
  case_type?: CaseType;
  sex?: SexFilter;
  state?: string;
  age_low?: number;
  age_high?: number;
  date_from?: string;
  date_to?: string;
}

export interface SearchRequest {
  query: string;
  filters?: SearchFilters;
  limit?: number;
}

// ── /search response (camelCase results, snake_case envelope) ─────────

export interface MatchMapping {
  queryTerm: string;
  forensicField: string;
  forensicValue: string;
  similarity: number;
}

export interface SearchResult {
  caseId: string;
  title: string;
  confidence: number;
  threshold: ConfidenceLabel;
  stateFound: string;
  genderEst: string;
  ageRange: string;
  discoveryDate: string;
  namusLink?: string | null;
  matchMappings: MatchMapping[];
}

export interface SearchResponse {
  query: string;
  total_matches: number;
  latency_ms: number;
  results: SearchResult[];
}

// ── /case/{id} response ───────────────────────────────────────────────

export interface CaseDetailResponse {
  case: CasePayload;
}

// ── /health response ──────────────────────────────────────────────────

export interface HealthResponse {
  status: "ok" | "degraded";
  vectorai_reachable: boolean;
  collection_exists: boolean;
  point_count: number | null;
}

// ── Error type ────────────────────────────────────────────────────────

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ── Internal request helper ───────────────────────────────────────────

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, signal } = opts;
  const url = `${API_BASE_URL}${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, `Network error: ${(err as Error).message ?? "request failed"}`);
  }

  if (!response.ok) {
    const text = await response.text();
    let errorBody: unknown = text;
    let message = `${method} ${path} → ${response.status}`;
    try {
      const json: unknown = JSON.parse(text);
      errorBody = json;
      const detail = (json as { detail?: unknown })?.detail;
      if (typeof detail === "string") message = detail;
    } catch {
      // body isn't JSON (e.g. nginx HTML error page) — raw text stays on errorBody
    }
    throw new ApiError(response.status, message, errorBody);
  }

  return (await response.json()) as T;
}

// ── Public API ────────────────────────────────────────────────────────

export function searchCases(
  req: SearchRequest,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  return request<SearchResponse>("/search", { method: "POST", body: req, signal });
}

export async function searchWithImage(
  image: File,
  form: {
    query: string;
    caseType: string;
    sex: string;
    state: string;
    ageLow: string;
    ageHigh: string;
    dateFrom: string;
    dateTo: string;
  },
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const fd = new FormData();
  fd.append("image", image);
  fd.append("query", form.query);
  if (form.caseType) fd.append("case_type", form.caseType);
  if (form.sex) fd.append("sex", form.sex);
  if (form.state) fd.append("state", form.state);
  if (form.ageLow) fd.append("age_low", form.ageLow);
  if (form.ageHigh) fd.append("age_high", form.ageHigh);
  if (form.dateFrom) fd.append("date_from", form.dateFrom);
  if (form.dateTo) fd.append("date_to", form.dateTo);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/search/image`, {
      method: "POST",
      body: fd,
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, `Network error: ${(err as Error).message ?? "request failed"}`);
  }

  if (!response.ok) {
    const text = await response.text();
    let message = `POST /search/image → ${response.status}`;
    try {
      const json = JSON.parse(text);
      if (typeof json.detail === "string") message = json.detail;
    } catch { /* raw text */ }
    throw new ApiError(response.status, message, text);
  }

  return (await response.json()) as SearchResponse;
}

export function getCase(
  caseId: string,
  signal?: AbortSignal,
): Promise<CaseDetailResponse> {
  return request<CaseDetailResponse>(
    `/case/${encodeURIComponent(caseId)}`,
    { signal },
  );
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>("/health", { signal });
}
