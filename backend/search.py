"""Hybrid search engine: multi-vector fan-out, RRF fusion, why-matched.

Single public function: ``run_search(req, client) -> SearchResponse``.
Caller owns the ``VectorAIClient`` (``main.py`` injects via ``Depends``).
"""
from __future__ import annotations

import re
import time
from datetime import datetime

import numpy as np
from actian_vectorai import ScoredPoint, VectorAIClient, reciprocal_rank_fusion

from config import (
    COLLECTION_NAME,
    PER_VECTOR_CANDIDATES,
    RRF_K,
    STATE_NAMES,
)
from embeddings import (
    embed_text_bge,
    embed_text_bge_batch,
    embed_text_clip,
    embed_text_sapbert,
)
from filters import build_filter
from schemas import (
    MatchMapping,
    SearchRequest,
    SearchResponse,
    SearchResult,
)


# ── Title / formatting helpers ────────────────────────────────────────


def _compose_title(payload: dict) -> str:
    """Build display title from payload, e.g. 'Unidentified Male (Found 2020)'."""
    sex = payload.get("sex", "Person")
    date_iso = payload.get("date_iso", "")
    year = date_iso[:4] if len(date_iso) >= 4 else "Unknown"
    if payload.get("case_type") == "unidentified":
        return f"Unidentified {sex} (Found {year})"
    return f"Missing {sex} (Reported {year})"


def _format_age(payload: dict) -> str:
    """Format age range for the card, e.g. ``'30 - 38 Years'``."""
    return f"{payload.get('age_low', '?')} - {payload.get('age_high', '?')} Years"


def _format_date(date_iso: str) -> str:
    """Convert ISO date to display format, e.g. ``'2020-06-02'`` -> ``'Jun 02, 2020'``."""
    try:
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return date_iso


# ── Query chunking ────────────────────────────────────────────────────


def _chunk_query(query: str) -> list[str]:
    """Split query on ``', '``, ``' and '``, ``'; '``; drop <3-char; cap 5."""
    parts = re.split(r",\s+|\s+and\s+|;\s+", query)
    chunks = [p.strip() for p in parts if len(p.strip()) >= 3]
    return chunks[:5]


# ── Fine-grained field labels ─────────────────────────────────────────

_MARK_RE = re.compile(
    r"tattoo|scar|mark|piercing|birthmark|mole|brand", re.I
)
_LOCATION_RE = re.compile(
    r"forearm|arm|leg|shoulder|chest|back|neck|ankle|wrist|hand|foot"
    r"|thigh|abdomen|face|torso|hip",
    re.I,
)
_BIO_RE = re.compile(
    r"\bage\b|\byear.?\s*old\b|\bfeet?\b|\binch|height|weight"
    r"|\blbs?\b|\bkg\b|stature|male|female",
    re.I,
)
_RECOVERY_RE = re.compile(
    r"highway|I-\d+|interstate|corridor|road|creek|river|lake|park"
    r"|bridge|trail|woods|forest|field|ditch|county|route",
    re.I,
)
_DATE_RE = re.compile(
    r"\b\d{4}\b|january|february|march|april|may|june|july|august"
    r"|september|october|november|december|\bdate\b",
    re.I,
)


def _classify_field(chunk: str, source_text: str, vector_name: str) -> str:
    """Assign a fine-grained forensic field label via keyword heuristics.

    Inspects both the query *chunk* and the matching *source_text* to pick
    a sub-field label (e.g. ``DISTINGUISHING_MARKS`` instead of the coarse
    ``PHYSICAL_DESCRIPTION``) that matches the frontend mock granularity.
    """
    combined = f"{chunk} {source_text}"
    if vector_name == "physical_text":
        if _MARK_RE.search(combined):
            return "DISTINGUISHING_MARKS"
        if _LOCATION_RE.search(combined):
            return "MARK_LOCATION"
        if _BIO_RE.search(combined):
            return "BIOLOGICAL_RELATION / AGE_EST"
        return "PHYSICAL_DESCRIPTION"
    if vector_name == "circumstances":
        if _RECOVERY_RE.search(combined):
            return "RECOVERY_LOCATION"
        if _DATE_RE.search(combined):
            return "DISCOVERY_DATE"
        return "CIRCUMSTANCES"
    if vector_name == "clothing":
        return "CLOTHING_EFFECTS"
    return vector_name.upper()


def _first_sentence(text: str, max_len: int = 80) -> str:
    """Extract the first sentence, truncated to *max_len* characters."""
    m = re.match(r"[^.!?]*[.!?]", text)
    snippet = m.group(0) if m else text
    if len(snippet) > max_len:
        return snippet[: max_len - 1] + "\u2026"
    return snippet


# ── Cosine similarity ─────────────────────────────────────────────────


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors. Returns 0.0 for zero vectors."""
    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


# ── Why This Matched ──────────────────────────────────────────────────


def _build_match_mappings(
    chunks: list[str],
    chunk_sap: list[list[float]],
    chunk_bge: list[list[float]],
    payload: dict,
) -> list[MatchMapping]:
    """Build the 'Why This Matched' rows for one result.

    Chunk embeddings are computed once by the caller and shared across
    all results so we only pay the embedding cost once per search.
    """
    if not chunks:
        return []

    sources: dict[str, str] = {}
    for key in ("physical_text", "circumstances", "clothing"):
        val = payload.get(key, "")
        if val:
            sources[key] = val
    if not sources:
        return []

    # Encode source texts (per-result cost)
    source_vecs: dict[str, list[float]] = {}
    if "physical_text" in sources:
        source_vecs["physical_text"] = embed_text_sapbert(sources["physical_text"])
    bge_keys = [k for k in ("circumstances", "clothing") if k in sources]
    if bge_keys:
        bge_vecs = embed_text_bge_batch([sources[k] for k in bge_keys])
        for k, v in zip(bge_keys, bge_vecs):
            source_vecs[k] = v

    mappings: list[MatchMapping] = []
    for i, chunk in enumerate(chunks):
        best_sim = -1.0
        best_key = ""
        best_label = ""

        for field_name, field_vec in source_vecs.items():
            cvec = chunk_sap[i] if field_name == "physical_text" else chunk_bge[i]
            sim = _cosine(cvec, field_vec)
            if sim > best_sim:
                best_sim = sim
                best_key = field_name
                best_label = _classify_field(
                    chunk, sources[field_name], field_name
                )

        if best_key:
            mappings.append(
                MatchMapping(
                    queryTerm=f'"{chunk}"',
                    forensicField=best_label,
                    forensicValue=_first_sentence(sources[best_key]),
                    similarity=_clamp01(best_sim),
                )
            )

    mappings.sort(key=lambda m: m.similarity, reverse=True)
    return mappings[:5]


# ── Score helpers ─────────────────────────────────────────────────────


def _clamp01(v: float) -> float:
    """Clamp *v* to ``[0.0, 1.0]`` — prevents Pydantic rejection on fp rounding."""
    return min(max(v, 0.0), 1.0)


# ── Main search function ─────────────────────────────────────────────


def run_search(req: SearchRequest, client: VectorAIClient) -> SearchResponse:
    """Execute hybrid multi-vector search with RRF fusion.

    Steps:
      1. Build hard metadata filter from request filters.
      2. Embed query three ways (SapBERT, BGE-M3, CLIP).
      3. Fan out four named-vector searches against ``cases``.
      4. Fuse with ``reciprocal_rank_fusion`` (ordering only).
      5. Compute ``confidence = max(per-vector cosine)``, build results.
    """
    t0 = time.perf_counter()

    # 1. Hard filter
    filter_ = build_filter(req.filters)

    # 2. Embed query
    q_sap = embed_text_sapbert(req.query)
    q_bge = embed_text_bge(req.query)
    q_clip = embed_text_clip(req.query)

    # 3. Fan-out: 4 named-vector searches
    common = dict(
        collection_name=COLLECTION_NAME,
        limit=PER_VECTOR_CANDIDATES,
        filter=filter_,
        with_payload=True,
    )

    hits_physical_text: list[ScoredPoint] = client.points.search(
        vector=q_sap, using="physical_text", **common
    )
    hits_physical_image: list[ScoredPoint] = client.points.search(
        vector=q_clip, using="physical_image", **common
    )
    hits_circumstances: list[ScoredPoint] = client.points.search(
        vector=q_bge, using="circumstances", **common
    )
    hits_clothing: list[ScoredPoint] = client.points.search(
        vector=q_bge, using="clothing", **common
    )

    # 4. RRF fusion (ordering only -- raw score ignored)
    all_lists = [
        hits_physical_text,
        hits_physical_image,
        hits_circumstances,
        hits_clothing,
    ]
    fused = reciprocal_rank_fusion(
        all_lists, limit=req.limit, ranking_constant_k=RRF_K
    )

    # Per-vector score lookup for confidence computation
    score_map: dict[str | int, dict[str, float]] = {}
    vector_names = ["physical_text", "physical_image", "circumstances", "clothing"]
    for vname, hit_list in zip(vector_names, all_lists):
        for sp in hit_list:
            score_map.setdefault(sp.id, {})[vname] = sp.score

    # Pre-compute chunk embeddings once for why-matched (shared across results)
    chunks = _chunk_query(req.query)
    chunk_sap = [embed_text_sapbert(c) for c in chunks] if chunks else []
    chunk_bge = embed_text_bge_batch(chunks) if chunks else []

    # 5. Build SearchResult list
    results: list[SearchResult] = []
    for point in fused:
        payload = point.payload or {}
        per_vector = score_map.get(point.id, {})
        confidence = _clamp01(max(per_vector.values())) if per_vector else 0.0

        match_mappings = _build_match_mappings(
            chunks, chunk_sap, chunk_bge, payload
        )

        results.append(
            SearchResult(
                caseId=payload.get("case_id", str(point.id)),
                title=_compose_title(payload),
                confidence=confidence,
                stateFound=STATE_NAMES.get(
                    payload.get("state", ""), payload.get("state", "")
                ),
                genderEst=payload.get("sex", "Unknown"),
                ageRange=_format_age(payload),
                discoveryDate=_format_date(payload.get("date_iso", "")),
                namusLink=None,
                matchMappings=match_mappings,
            )
        )

    latency_ms = int((time.perf_counter() - t0) * 1000)

    return SearchResponse(
        query=req.query,
        total_matches=len(results),
        latency_ms=latency_ms,
        results=results,
    )
