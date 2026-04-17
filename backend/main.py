"""Trace FastAPI server.

Endpoints:
  POST /search      — hybrid semantic search
  GET  /case/{id}   — fetch a single case by human case_id (e.g. 'MP-001')
  GET  /health      — readiness probe (responds even when DB is down)

Design notes:
  * All endpoints that need the DB use Depends(get_client) except /health,
    which must respond even when the DB is None (PLAN.md § 2.9).
  * run_search() and embed_* are CPU-bound sync functions. FastAPI runs sync
    `def` endpoints in a threadpool automatically — never blocks event loop.
  * Embedders are pre-warmed via asyncio.to_thread in lifespan so the first
    search doesn't incur a ~19s cold-start model-load penalty.
  * VectorAIClient is opened via to_thread(__enter__)/(__exit__) — the SDK
    only exposes a context-manager lifecycle and its enter/exit do gRPC IO,
    which would block the event loop if invoked synchronously.
  * Lifespan is fault-tolerant: warmup or DB-connect failures log and leave
    `_client = None` so /health still responds and /search returns 503.
"""
from __future__ import annotations

import asyncio
import logging
import tempfile
from contextlib import asynccontextmanager

from actian_vectorai import Field, FilterBuilder, VectorAIClient
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import COLLECTION_NAME, FRONTEND_ORIGINS, VECTORAI_ADDR
from embeddings import embed_image_clip, embed_text_bge, embed_text_clip, embed_text_sapbert
from schemas import (
    CaseDetailResponse,
    CasePayload,
    HealthResponse,
    SearchFilters,
    SearchRequest,
    SearchResponse,
)
from search import run_search

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB

logger = logging.getLogger("trace.main")


# ── DB client singleton ───────────────────────────────────────────────

_client: VectorAIClient | None = None


def get_client() -> VectorAIClient:
    """Dependency: raises HTTP 503 (not AssertionError) when DB is unavailable."""
    if _client is None:
        raise HTTPException(status_code=503, detail="Database client not available")
    return _client


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm embedders, open DB connection, always reach yield.

    Both warmup and DB-connect failures are caught and logged so the app
    still starts and /health can report degraded state. Lazy embedders
    will load on first request if warmup failed; /search returns 503 via
    get_client() if DB connect failed.

    Lifecycle uses to_thread(__enter__/__exit__) — the SDK only documents
    a context-manager interface, and its enter/exit do gRPC IO that would
    otherwise block the event loop.
    """
    global _client

    try:
        await asyncio.gather(
            asyncio.to_thread(embed_text_sapbert, "warmup"),
            asyncio.to_thread(embed_text_bge, "warmup"),
            asyncio.to_thread(embed_text_clip, "warmup"),
        )
    except Exception as exc:
        logger.warning(
            "embedding warmup failed: %r — models will load lazily on first request",
            exc,
        )

    client: VectorAIClient | None = None
    try:
        client = VectorAIClient(VECTORAI_ADDR)
        await asyncio.to_thread(client.__enter__)
        _client = client
    except Exception as exc:
        logger.error(
            "DB connect failed at startup: %r — /search returns 503 until DB recovers",
            exc,
        )
        client = None
        _client = None

    try:
        yield
    finally:
        if client is not None:
            try:
                await asyncio.to_thread(client.__exit__, None, None, None)
            except Exception as exc:
                logger.warning("DB shutdown error: %r", exc)
        _client = None


# ── App + middleware ──────────────────────────────────────────────────

app = FastAPI(title="Trace", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)


# ── Endpoints ─────────────────────────────────────────────────────────

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, client: VectorAIClient = Depends(get_client)):
    """Hybrid multi-vector search with RRF fusion."""
    return run_search(req, client)


@app.post("/search/image", response_model=SearchResponse)
def search_with_image(
    image: UploadFile = File(...),
    query: str = Form(""),
    case_type: str = Form(""),
    sex: str = Form(""),
    state: str = Form(""),
    age_low: str = Form(""),
    age_high: str = Form(""),
    date_from: str = Form(""),
    date_to: str = Form(""),
    client: VectorAIClient = Depends(get_client),
):
    """Search with an uploaded image via CLIP cross-modal matching."""
    data = image.file.read(MAX_IMAGE_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 10 MB limit")

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            img_vec = embed_image_clip(tmp.name)
        except Exception as exc:
            logger.error("image embedding failed: %r", exc)
            raise HTTPException(status_code=500, detail=f"Image embedding failed: {exc}") from exc

    filters: dict = {}
    if case_type:
        filters["case_type"] = case_type
    if sex:
        filters["sex"] = sex
    if state:
        filters["state"] = state
    try:
        if age_low:
            filters["age_low"] = int(age_low)
        if age_high:
            filters["age_high"] = int(age_high)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid age value: {exc}") from exc
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    req = SearchRequest(
        query=query if query.strip() else "image search",
        filters=SearchFilters(**filters) if filters else None,
    )
    return run_search(req, client, image_vec=img_vec)


@app.get("/case/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: str, client: VectorAIClient = Depends(get_client)):
    """Fetch a single case by its human case_id (e.g. 'MP-001').

    Scrolls with a payload filter on the `case_id` field — point IDs in
    Actian are UUID5 values derived at ingest time (see ingest.py), so a
    direct point lookup by case_id string is not possible.

    scroll() returns (points_list, next_cursor) as a tuple in this SDK
    version; unpacked defensively in case a future release returns a plain list.

    Empty payloads return 404 (the case is functionally missing). Payloads
    that fail Pydantic validation return 500 with a clear message.
    """
    fb = FilterBuilder()
    fb.must(Field("case_id").eq(case_id))

    try:
        scroll_result = client.points.scroll(
            COLLECTION_NAME,
            filter=fb.build(),
            limit=1,
            with_payload=True,
        )
    except Exception as exc:
        logger.error("case lookup failed for %r: %r", case_id, exc)
        raise HTTPException(status_code=503, detail="Database query failed") from exc

    if isinstance(scroll_result, tuple):
        points, _ = scroll_result
    else:
        points = scroll_result

    if not points:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    payload = points[0].payload
    if not payload:
        raise HTTPException(
            status_code=404, detail=f"Case '{case_id}' has no payload data"
        )

    try:
        case = CasePayload.model_validate(payload)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Payload validation error: {exc}"
        ) from exc

    return CaseDetailResponse(case=case)


@app.get("/health", response_model=HealthResponse)
def health():
    """Readiness probe.

    Intentionally does NOT use Depends(get_client) so it responds 'degraded'
    even when the DB client is None — the frontend and docker healthcheck both
    poll this before the DB may be available.
    """
    try:
        reachable = _client is not None
        exists = _client.collections.exists(COLLECTION_NAME) if reachable else False
        count = _client.points.count(COLLECTION_NAME) if exists else None
    except Exception as exc:
        logger.warning("health check failed: %r", exc)
        reachable, exists, count = False, False, None

    return HealthResponse(
        status="ok" if (reachable and exists) else "degraded",
        vectorai_reachable=reachable,
        collection_exists=exists,
        point_count=count,
    )
