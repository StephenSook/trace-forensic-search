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


# ── Actian VectorAI DB ────────────────────────────────────────────────

VECTORAI_HOST = os.getenv("VECTORAI_HOST", "localhost")
VECTORAI_PORT = int(os.getenv("VECTORAI_PORT", "50051"))
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

DEFAULT_LIMIT = 10
RRF_K = 60  # ranking_constant_k for reciprocal_rank_fusion


# ── Paths ─────────────────────────────────────────────────────────────

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYNTHETIC_CASES_PATH = os.path.join(REPO_ROOT, "data", "synthetic", "cases.json")


# ── CORS (frontend origin) ────────────────────────────────────────────

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
