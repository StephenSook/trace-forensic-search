"""Trace ingest pipeline.

Reads synthetic cases, computes four named vectors per case, upserts to
Actian VectorAI DB. Idempotent — re-running with the same input replays
the same `case_id`s, overwriting vectors + payloads in place.

Embedding functions are injected via `Embedders` so this module can be
exercised end-to-end before `embeddings.py` (Vinh's file) lands. When
Vinh ships, `main()` picks up the real functions and nothing here
changes.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from actian_vectorai import (
    Distance,
    PointStruct,
    VectorAIClient,
    VectorParams,
)

from config import COLLECTION_NAME, SYNTHETIC_CASES_PATH, VECTORAI_ADDR, VECTORS
from schemas import CasePayload, IngestResponse


TextEmbedder = Callable[[str], list[float]]
ImageEmbedder = Callable[[str], list[float]]  # path string or URL

# Actian requires UUID point IDs. Deriving one from the human-readable
# case_id keeps ingest idempotent — re-running overwrites the same point
# — while the original id stays on the payload for display + filtering.
_CASE_ID_NAMESPACE = uuid.UUID("6c7b1f1e-5f1a-4b8e-9a3f-7d2c5e6b8a01")


def point_id_for(case_id: str) -> str:
    """Stable UUID5 derived from a human case_id (e.g. 'MP-001')."""
    return str(uuid.uuid5(_CASE_ID_NAMESPACE, case_id))


@dataclass
class Embedders:
    """Three pluggable embed functions. Dims must match `config.VECTORS`."""

    sapbert: TextEmbedder       # 768-dim — physical_text
    bge: TextEmbedder           # 1024-dim — circumstances + clothing
    clip_image: ImageEmbedder   # 512-dim — physical_image (optional)


# ── Loading ──────────────────────────────────────────────────────────

def load_cases(path: str | Path = SYNTHETIC_CASES_PATH) -> list[CasePayload]:
    """Read the synthetic cases JSON and validate every record."""
    with open(path) as f:
        raw = json.load(f)
    return [CasePayload.model_validate(c) for c in raw]


# ── Collection setup ────────────────────────────────────────────────

def ensure_collection(client: VectorAIClient) -> bool:
    """Create `cases` with four named-vector specs if it doesn't exist.

    Returns True if a new collection was created, False if it already
    existed.
    """
    if client.collections.exists(COLLECTION_NAME):
        return False
    client.collections.create(
        COLLECTION_NAME,
        vectors_config={
            name: VectorParams(size=spec.dim, distance=Distance.Cosine)
            for name, spec in VECTORS.items()
        },
    )
    return True


# ── Point construction ─────────────────────────────────────────────

def build_point(case: CasePayload, emb: Embedders) -> PointStruct:
    """Turn one case into a multi-vector PointStruct.

    `physical_image` is only populated when the case has an `image_url`
    — the Actian SDK accepts partial named-vector points.
    """
    vectors: dict[str, list[float]] = {
        "physical_text": emb.sapbert(case.physical_text),
        "circumstances": emb.bge(case.circumstances),
        "clothing": emb.bge(case.clothing),
    }
    if case.image_url:
        vectors["physical_image"] = emb.clip_image(case.image_url)

    return PointStruct(
        id=point_id_for(case.case_id),
        vector=vectors,
        payload=case.model_dump(),
    )


# ── Orchestrator ────────────────────────────────────────────────────

def run_ingest(
    client: VectorAIClient,
    cases: list[CasePayload],
    emb: Embedders,
    batch_size: int = 256,
) -> IngestResponse:
    """Full ingest path: ensure collection, embed every case, batched upsert.

    Returns the response envelope our ingest CLI + future `/ingest`
    endpoint expect.
    """
    t0 = time.perf_counter()
    ensure_collection(client)
    points = [build_point(c, emb) for c in cases]
    total = client.upload_points(COLLECTION_NAME, points, batch_size=batch_size)
    took_ms = int((time.perf_counter() - t0) * 1000)
    return IngestResponse(
        collection=COLLECTION_NAME,
        ingested=total,
        skipped=len(cases) - total,
        took_ms=took_ms,
    )


# ── Real embedder wiring (lazy import — Vinh's file) ───────────────

def _load_real_embedders() -> Embedders:
    """Pull the three embed functions from Vinh's `embeddings.py`.

    Import is deferred so this module stays importable — and testable —
    before `embeddings.py` is written.
    """
    from embeddings import embed_text_sapbert, embed_text_bge, embed_image_clip
    return Embedders(
        sapbert=embed_text_sapbert,
        bge=embed_text_bge,
        clip_image=embed_image_clip,
    )


# ── CLI ─────────────────────────────────────────────────────────────

def main() -> None:
    cases = load_cases()
    emb = _load_real_embedders()
    with VectorAIClient(VECTORAI_ADDR) as client:
        resp = run_ingest(client, cases, emb)
    print(
        f"✓ ingested {resp.ingested}/{len(cases)} cases "
        f"→ collection '{resp.collection}' "
        f"in {resp.took_ms}ms "
        f"(skipped {resp.skipped})"
    )


if __name__ == "__main__":
    main()
