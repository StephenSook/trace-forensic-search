"""Pydantic models for Trace's FastAPI surface.

Two shapes live here and are deliberately different:

    * `CasePayload` — snake_case. This is what we store in Actian as
      `point.payload` and what ingest.py / search.py pass around in
      Python. Matches PLAN.md § 2.3.

    * `SearchResult` / `MatchMapping` — camelCase. These are the wire
      shape the React card component already consumes as props (see
      `frontend/src/components/TraceResultCard.tsx`). Keeping the wire
      contract aligned to the component props means zero runtime
      transform in the frontend.

Filter/response envelope field names mirror PLAN.md § 2.4 exactly so
Vinh's filter-builder (PLAN.md § 2.6) wires up without drift.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator


CaseType = Literal["missing", "unidentified"]
Sex = Literal["Male", "Female"]
# Filter-side sex allows "Unknown" — many records don't have it pinned.
SexFilter = Literal["Male", "Female", "Unknown"]

ConfidenceLabel = Literal["HIGH CONFIDENCE", "MEDIUM CONFIDENCE", "LOW CONFIDENCE"]

_ISO_DATE_RE = r"^\d{4}-\d{2}-\d{2}$"
_STATE_RE = r"^[A-Z]{2}$"


# ── Canonical case payload (what lives in Actian as point.payload) ────

class CasePayload(BaseModel):
    """One record in the `cases` collection. Produced by ingest.py,
    consumed by search.py, shared between Stephen and Vinh."""

    case_id: str
    case_type: CaseType
    sex: Sex
    age_low: int = Field(ge=0, le=120)
    age_high: int = Field(ge=0, le=120)
    state: str = Field(pattern=_STATE_RE)

    # Dates: store both per O4. Filter against date_epoch, display date_iso.
    date_epoch: int
    date_iso: str = Field(pattern=_ISO_DATE_RE)

    physical_text: str
    circumstances: str
    clothing: str
    image_url: str | None = None

    @model_validator(mode="after")
    def _check_age_order(self) -> "CasePayload":
        if self.age_low > self.age_high:
            raise ValueError(
                f"age_low ({self.age_low}) must be ≤ age_high ({self.age_high})"
            )
        return self


# ── /search request ───────────────────────────────────────────────────

class SearchFilters(BaseModel):
    case_type: CaseType | None = None
    sex: SexFilter | None = None
    state: str | None = Field(default=None, pattern=_STATE_RE)
    age_low: int | None = Field(default=None, ge=0, le=120)
    age_high: int | None = Field(default=None, ge=0, le=120)
    date_from: str | None = Field(default=None, pattern=_ISO_DATE_RE)
    date_to: str | None = Field(default=None, pattern=_ISO_DATE_RE)

    @model_validator(mode="after")
    def _check_ranges(self) -> "SearchFilters":
        if (
            self.age_low is not None
            and self.age_high is not None
            and self.age_low > self.age_high
        ):
            raise ValueError(
                f"age_low ({self.age_low}) must be ≤ age_high ({self.age_high})"
            )
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError(
                f"date_from ({self.date_from}) must be ≤ date_to ({self.date_to})"
            )
        return self


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    filters: SearchFilters | None = None
    limit: int = Field(default=10, ge=1, le=50)


# ── /search response ──────────────────────────────────────────────────
#
# camelCase on purpose — mirrors TraceResultCardProps so the card can
# consume results without a transform layer.

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
    stateFound: str
    genderEst: str
    ageRange: str                      # e.g. "30–38"
    discoveryDate: str                 # human-formatted, e.g. "2020-06-02"
    namusLink: str | None = None
    matchMappings: list[MatchMapping] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def threshold(self) -> ConfidenceLabel:
        if self.confidence >= 0.85:
            return "HIGH CONFIDENCE"
        if self.confidence >= 0.6:
            return "MEDIUM CONFIDENCE"
        return "LOW CONFIDENCE"


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    latency_ms: int
    results: list[SearchResult]


# ── /case/{id} response ───────────────────────────────────────────────

class CaseDetailResponse(BaseModel):
    case: CasePayload


# ── /ingest response (used by Stephen's ingest path) ──────────────────

class IngestResponse(BaseModel):
    collection: str
    ingested: int
    skipped: int = 0
    took_ms: int


# ── /health ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = "ok"
    vectorai_reachable: bool
    collection_exists: bool
    point_count: int | None = None
