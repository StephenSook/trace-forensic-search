"""Pydantic models for Trace's FastAPI surface.

Kept small and UI-shaped: request/response types here mirror the props
the frontend components already consume (see
`frontend/src/components/TraceResultCard.tsx`). The ingest-side case
shape is also declared here so ingest.py and search.py agree on the
payload contract with zero drift.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


CaseType = Literal["missing", "unidentified"]
Sex = Literal["Male", "Female"]


# ── Canonical case payload (what lives in Actian as point.payload) ────

class CasePayload(BaseModel):
    """One record in the `cases` collection. Produced by ingest.py,
    consumed by search.py, shared between Stephen and Vinh."""

    case_id: str
    case_type: CaseType
    sex: Sex
    age_low: int = Field(ge=0, le=120)
    age_high: int = Field(ge=0, le=120)
    state: str = Field(min_length=2, max_length=2)  # 2-letter US code

    # Dates: store both per O4. Filter against date_epoch, display date_iso.
    date_epoch: int
    date_iso: str  # "YYYY-MM-DD"

    physical_text: str
    circumstances: str
    clothing: str
    image_url: str | None = None


# ── /search request ───────────────────────────────────────────────────

class DateRange(BaseModel):
    start_iso: str | None = None   # "YYYY-MM-DD"
    end_iso: str | None = None


class SearchFilters(BaseModel):
    case_type: CaseType | None = None
    sex: Sex | None = None
    state: str | None = None
    age_min: int | None = Field(default=None, ge=0, le=120)
    age_max: int | None = Field(default=None, ge=0, le=120)
    date: DateRange | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    filters: SearchFilters | None = None
    limit: int = Field(default=10, ge=1, le=50)


# ── /search response ──────────────────────────────────────────────────
#
# Shape deliberately mirrors TraceResultCardProps (frontend).

class MatchMapping(BaseModel):
    """One row of the 'Why This Matched' table."""

    queryTerm: str
    forensicField: str
    forensicValue: str
    similarity: float = Field(ge=0.0, le=1.0)


class SearchResult(BaseModel):
    caseId: str
    title: str
    confidence: float = Field(ge=0.0, le=1.0)
    threshold: str                     # e.g. "HIGH CONFIDENCE"
    stateFound: str
    genderEst: str
    ageRange: str                      # e.g. "30–38"
    discoveryDate: str                 # human-formatted, e.g. "2020-06-02"
    namusLink: str | None = None
    matchMappings: list[MatchMapping] = []


class SearchResponse(BaseModel):
    query: str
    total: int
    took_ms: int
    results: list[SearchResult]


# ── /case/{id} response ───────────────────────────────────────────────

class CaseDetailResponse(BaseModel):
    case: CasePayload


# ── /health ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    vectorai_reachable: bool
    collection_exists: bool
    point_count: int | None = None
