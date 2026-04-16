"""Central configuration for Trace backend.

All constants shared across ingest / search / main live here so there is
exactly one source of truth. Environment variables override defaults for
host/port only; model IDs and vector dims are fixed by the architecture.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    """Parse an int env var with a loud, specific error on bad input.

    Bare `int(os.getenv(...))` crashes with an opaque `ValueError` at
    import time if the env is malformed — painful to debug when three
    services all load the same config.
    """
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Env var {name!r}={raw!r} is not a valid integer"
        ) from exc


# ── Actian VectorAI DB ────────────────────────────────────────────────

VECTORAI_HOST = os.getenv("VECTORAI_HOST", "localhost")
VECTORAI_PORT = _int_env("VECTORAI_PORT", 50051)
VECTORAI_ADDR = f"{VECTORAI_HOST}:{VECTORAI_PORT}"


# ── Collection ────────────────────────────────────────────────────────

COLLECTION_NAME = "cases"


# ── Named vector spaces ───────────────────────────────────────────────
#
# Each point in `cases` carries up to four named vectors. Dims are
# locked by the embedding model choice (see MODEL_IDS below).

@dataclass(frozen=True)
class VectorSpec:
    name: str
    dim: int
    model_id: str


VECTORS: dict[str, VectorSpec] = {
    "physical_text": VectorSpec(
        name="physical_text",
        dim=768,
        model_id="cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
    ),
    "physical_image": VectorSpec(
        name="physical_image",
        dim=512,
        model_id="openai/clip-vit-base-patch32",
    ),
    "circumstances": VectorSpec(
        name="circumstances",
        dim=1024,
        model_id="BAAI/bge-m3",
    ),
    "clothing": VectorSpec(
        name="clothing",
        dim=1024,
        model_id="BAAI/bge-m3",
    ),
}


# ── Model IDs (convenience aliases used by embeddings.py) ─────────────

SAPBERT_MODEL_ID = VECTORS["physical_text"].model_id
CLIP_MODEL_ID = VECTORS["physical_image"].model_id
BGE_M3_MODEL_ID = VECTORS["circumstances"].model_id


# ── Search defaults ───────────────────────────────────────────────────

# NB: default result limit lives on SearchRequest.limit (schemas.py).
# Kept here only because ingest + health probes reference it.
RRF_K = 60  # ranking_constant_k for reciprocal_rank_fusion
PER_VECTOR_CANDIDATES = 25  # fan-out pool size before RRF fusion


# ── Paths ─────────────────────────────────────────────────────────────

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYNTHETIC_CASES_PATH = os.path.join(REPO_ROOT, "data", "synthetic", "cases.json")


# ── US state abbreviation → full name (50 states + DC) ───────────────

STATE_NAMES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


# ── CORS (frontend origin) ────────────────────────────────────────────

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
