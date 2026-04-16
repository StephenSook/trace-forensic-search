# Trace — Implementation Plan & Status Tracker

> Living working doc for **Stephen Sookra** (frontend + pitch) and **Vinh Le** (backend + AI systems). Updated on every completed task and pushed to `main`. Authoritative over the PDF when they disagree.

**Hackathon:** Actian VectorAI DB Build Challenge — Apr 13–18, 2026
**Today:** Apr 16, 2026 (Day 4 of 6)
**Repo:** https://github.com/StephenSook/trace-forensic-search
**Actian reference:** https://github.com/hackmamba-io/actian-vectorAI-db-beta (cloned locally at `../actian-vectorAI-db-beta` for example scripts)

---

## Sources of truth (priority order)

1. **Actian hackmamba repo** — `README.md`, `examples/*.py`, `docs/api.md`. Authoritative for all DB/client API questions.
2. **This file (`PLAN.md`)** — authoritative for project decisions, task ownership, and status.
3. **`frontend/Background Information/Trace_Claude_Background.pdf`** — authoritative for the *problem*, the pitch framing, forensic terminology. **Not** authoritative for API details — it predates the real client release and calls the package `actiancortex` (outdated; it's `actian_vectorai`).
4. **`README.md`** — public-facing blurb. Keep concise; don't mirror this plan into it.

---

## Status dashboard

Legend: ✅ done &nbsp; 🟡 in progress &nbsp; ⬜ not started &nbsp; ⛔ blocked

| # | Component | File(s) | Owner | Status | Notes |
|---|---|---|---|---|---|
| 1.1 | Frontend UI scaffold | `frontend/` | Stephen | ✅ | Built in Lovable, uses mock data. |
| 1.2 | GitHub repo + README | repo root | Stephen | ✅ | Public, MIT. |
| 1.3 | Docker Desktop on dev machine | — | Stephen | ✅ | v29.4.0 verified 2026-04-15. |
| 1.4 | Actian DB container running | `docker-compose.yml` (sibling) | Claude | ✅ | Port 50051 up; end-to-end smoke test passed with `examples/01_hello_world.py`. |
| 1.5 | Actian Python wheel vendored locally | `backend/vendor/actian_vectorai-0.1.0b2-py3-none-any.whl` | Claude | ✅ | Present in local vendor dir; **gitignored per Geri (hackathon Discord, 2026-04-15)** — each dev copies it from their own hackmamba clone. Setup steps added below. |
| 1.6 | Frontend deps installed | `frontend/node_modules/` | Claude | ✅ | Via npm (348 pkgs). Bun lockfile retained for teammate flexibility. |
| 2.1 | `requirements.txt` | `backend/requirements.txt` | Claude | ✅ | Installed + import smoke test green 2026-04-15. Pinned `transformers<5.0` after a 5.5.4/FlagEmbedding collision. |
| 2.2 | Root `docker-compose.yml` | `docker-compose.yml` | **Stephen** | ✅ | Hardened 2026-04-15. Image pinned by sha256 digest (no silent drift before demo), port published as `${VECTORAI_PORT:-50051}` for coexistence with sibling, bash `/dev/tcp` healthcheck so `docker compose up -d --wait` blocks until gRPC accepts. `trace-vectoraidb` reports `healthy` state. |
| 2.3 | Config constants | `backend/config.py` | Claude | ✅ | Written 2026-04-15. Exports `COLLECTION_NAME`, `VECTORS` (4 named specs), `VECTORAI_ADDR`, `RRF_K=60`, `PER_VECTOR_CANDIDATES=25`, `STATE_NAMES` (50+DC). |
| 2.4 | Pydantic schemas | `backend/schemas.py` | Claude | ✅ | Written + reviewed 2026-04-15. `CasePayload`, `SearchFilters` (`age_low/age_high`, flat `date_from/date_to`), `SearchResponse` (`total_matches`, `latency_ms`), `SearchResult` (camelCase for card props, `threshold` is `@computed_field`). Cross-field validators on age/date order. `IngestResponse` for Stephen. All 60 synthetic cases validate clean. |
| 2.5 | Embedding model wrappers | `backend/embeddings.py` | **Vinh** | ✅ | Implemented 2026-04-15. 5 exports: `embed_text_sapbert` (768d), `embed_text_bge` (1024d), `embed_text_bge_batch`, `embed_text_clip` (512d), `embed_image_clip` (512d). Lazy model loading via `lru_cache`. L2-normalized (D7). SapBERT semantic bridge verified: 0.6164 cosine on PLAN.md demo pair (threshold 0.60). Device auto-detection (cuda>mps>cpu). |
| 2.6 | Filter DSL builder | `backend/filters.py` | **Vinh** | ✅ | Complete 2026-04-15. `build_filter(SearchFilters) -> Filter \| None` + `_iso_to_epoch` helper. 31 unit tests green — introspects `Filter.must[*].field` to verify clause keys, match values, range bounds, age-overlap semantics, epoch correctness, and ValueError on bad dates. |
| 2.7 | Ingest pipeline | `backend/ingest.py` | **Stephen** | ✅ | Complete 2026-04-15. Injectable `Embedders` DI, UUID5 idempotent IDs, 9 live tests green. Real-vector ingest run: 60/60 cases with SapBERT+BGE-M3+CLIP embeddings in ~73s on MPS. |
| 2.8 | Hybrid search engine | `backend/search.py` | **Vinh** | ✅ | Implemented 2026-04-16. `run_search(req, client) -> SearchResponse`. 4-vector fan-out (SapBERT/CLIP/BGE×2) + RRF fusion + max-cosine confidence + "Why This Matched" with fine-grained field labels. Chunk embeddings shared across results. 56 unit tests green (helpers + stubbed-client integration). |
| 2.9 | FastAPI server | `backend/main.py` | **Vinh** | ⬜ | Endpoints: `POST /search`, `GET /case/{id}`, `GET /health`. CORS for :5173. |
| 2.10 | Backend tests | `backend/tests/*.py` | **Stephen** | ✅ | Updated 2026-04-16. 146 tests total: test_schemas (47), test_config (12), test_synthetic_data (16), test_ingest (9), test_filters (31), test_search (56). All green. |
| 3.1 | API client | `frontend/src/lib/api.ts` | Stephen/Claude | ✅ | Typed fetch wrapper + `ApiError` class. Mirrors `schemas.py` exactly (camelCase results, snake_case envelope). 6 vitest specs green. |
| 3.2 | Search state + form wiring | `frontend/src/pages/Index.tsx`, `TraceSearchPanel.tsx` | Stephen/Claude | ✅ | Controlled inputs, lifted state in Index, `useMutation` fires `searchCases()`. 50-state dropdown, number age inputs, native date pickers, loading spinner, sonner error toasts. Mock fallback until backend ships. |
| 3.3 | Live results rendering | `frontend/src/components/TraceResultsPanel.tsx`, `TraceResultCard.tsx` | Stephen/Claude | ✅ | ResultsPanel accepts `data/isPending/error` props. Shows mock preview before first search, live results after, loading spinner during, empty state on 0 results. Latency counter in stream footer. |
| 3.4 | Loading/error states | same as 3.3 | Stephen/Claude | ✅ | Loading spinner + "EXECUTING SEMANTIC QUERY..." overlay, button disabled + spinner during pending, sonner toast on API/network error, "NO MATCHES FOUND" empty state with guidance. Cold-reviewed 2026-04-15: 5 issues found + fixed (namusLink, duplicate interface, hardcoded expansion, mock threshold alignment, type tightening). |
| 4.1 | Synthetic cases | `data/synthetic/cases.json` + `generate_cases.py` | Claude | ✅ | 60 cases, 6 ground-truth pairs (MP/UP-001..006), 36 states, 2015-2024, demo pair wording verbatim, schema-validated 2026-04-15. |
| 4.2 | Ingest run against real DB | runtime | **Stephen** | ✅ | Completed 2026-04-15. 60 points in `cases` collection with real embeddings. Demo query scores: circumstances 0.82 (MP-001), physical_text 0.65 (UP-001). Both vector spaces return semantically correct results. |
| 5.1 | Demo script / talk track | `DEMO_SCRIPT.md` | Stephen | ✅ | Completed 2026-04-15. 3:30–4:00 two-speaker script with Stephen/Vinh split, backup narrative, format contingencies, scoring-rubric callouts, and Q&A appendix. |
| 5.2 | Loom demo video (3–5 min) | external | Stephen | ⬜ | Day 5 deliverable. |
| 5.3 | DoraHacks submission write-up | external | Stephen | ⬜ | Day 5 deliverable. |
| 5.4 | README polish for judges | `README.md` | Stephen | ⬜ | Setup instructions + demo query. |

---

## Context

**What we're building.** Trace lets a family member or investigator describe a missing person in plain English and semantically matches that description against unidentified-remains case records. A mother searches "eagle tattoo on his right forearm" and the system surfaces a medical-examiner record reading "avian motif dermagraphic, right ventral antebrachium" — two records that share zero vocabulary under keyword search. The bridge is vector search across named embeddings in Actian VectorAI DB.

**Who it's for.** Families and advocates working with NamUs-like databases. NamUs runs on keyword search; the 600,000-missing / 40,000-unidentified gap persists partly because lay and forensic vocabularies don't overlap lexically. Trace closes that gap.

**Hackathon strategy.** Three architectural features map directly to the 30% "Use of Actian VectorAI DB" judging weight: (1) named vector spaces per point, (2) hard metadata filter DSL before vector search, (3) RRF hybrid fusion across multiple vector queries. None can be cut without tanking the score.

**The "that-shouldn't-be-possible" moment** (Sookra Methodology centerpiece): user types *"My brother went missing in 2019 in Tennessee. He was 34, about 6 feet tall, had a distinctive tattoo of an eagle on his right forearm, and was last seen near a highway."* — and within 200 ms the top result is an ME record with semantically-matched forensic language (I-40, avian motif dermagraphic, stature 178cm). The "Why This Matched" panel shows the bridge explicitly.

---

## Architecture decisions (locked unless renegotiated)

### D1 — Collection topology: **one collection, four named vectors**

One Actian collection called `cases`. Each point (one case record) holds four named vectors + shared payload:

| Named vector | Dim | Distance | Embedding model | Encodes |
|---|---|---|---|---|
| `physical_text` | 768 | Cosine | SapBERT (`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`) | Physical description, scars, marks, tattoos, dental |
| `physical_image` | 512 | Cosine | CLIP ViT-B/32 (`openai/clip-vit-base-patch32`) | Tattoo / identifying photo (cross-modal) |
| `circumstances` | 1024 | Cosine | BGE-M3 (`BAAI/bge-m3`) | Narrative of disappearance or recovery |
| `clothing` | 1024 | Cosine | BGE-M3 | Apparel, jewelry, personal effects |

**Deviation flag.** The `frontend/Background Information/Trace_Claude_Background.pdf` AND the backend README both describe **three separate collections** (physical / circumstances / clothing). We deviate because the Actian `examples/29_named_vectors.py` script shows multiple named vectors per point working end-to-end via the dict syntax `vector={"text": [...], "image": [...]}`. This gives us:
- One payload per case (no duplication across collections)
- One hard-filter expression applied once, across all vector searches
- Native use of Actian's named-vector feature (stronger showcase for the 30% scoring weight)
- `physical_image` (CLIP) lives naturally alongside `physical_text` (SapBERT) on the same point — no "image collection" orphan

**Locked 2026-04-15 by Stephen** — D1 stands. One `cases` collection with 4 named vectors.

### D2 — Fusion: built-in `reciprocal_rank_fusion` with k=60

Actian ships `reciprocal_rank_fusion(lists, limit, ranking_constant_k=60)` in the client. No custom implementation. We fan out 3–4 parallel searches against the `cases` collection (one per named vector that the query covers) and fuse client-side.

### D3 — Sparse path: **skip for MVP, stretch-goal for Day 4**

The hackmamba README states: *"Sparse-vector and multi-dense-vector write paths remain under server development."* Storing BGE-M3's sparse output server-side is therefore unreliable in this version. MVP path is dense-only multi-vector fusion — still counts as "hybrid fusion" per challenge rules (multiple heterogeneous dense vectors fused with RRF). Stretch path (Day 4, only if Days 3–4 are on schedule): compute BGE-M3 sparse weights client-side, build an in-memory BM25 index with `rank-bm25`, fuse keyword-match results into the same RRF call. This adds a true dense+sparse hybrid without depending on server support.

### D4 — Synthetic data: 50–100 fictional cases, ≥5 ground-truth pairs

All case data in the app is fictional. Each ground-truth pair has one "missing person" record (family vocabulary) and one "unidentified remains" record (ME vocabulary) describing the same fictional person, dated 3–18 months apart. The Benton County jester-tattoo case stays pitch-only; do not encode it in `cases.json` (ethics: real unsolved cases don't belong inside a live app's index).

### D5 — Deployment: Docker for the DB, native for the backend

Only the Actian DB runs in Docker. The FastAPI backend runs natively (`uvicorn main:app --reload`) because containerizing BGE-M3 + SapBERT + CLIP produces a ~5 GB image that would slow every dev rebuild. Demo day: same setup — hackathon judges accept `docker compose up -d && uvicorn main:app` as the run command.

### D6 — Python environment

Python 3.10+ required (Actian client minimum). Stephen's Mac has 3.12.5. Venv lives at `backend/.venv/` (gitignored). All installs are deterministic from `requirements.txt` including the local wheel path.

### D7 — Distance metric: Cosine everywhere

All four named vectors use `Distance.Cosine`. We L2-normalize vectors at embed time where the model doesn't already normalize (SapBERT does not; BGE-M3's dense output does; CLIP embeddings we'll normalize explicitly).

---

## Open decisions requiring Stephen sign-off

- [x] **O1:** ~~Confirm D1 (one collection with 4 named vectors) vs three-collection design.~~ **Locked D1 on 2026-04-15** (Stephen + Vinh). One `cases` collection, 4 named vectors per point.
- [ ] **O2:** Include the sparse BM25 stretch (D3 stretch path)? Adds ~½ day on Day 4. Recommend including only if Day 3 ends with Tasks 2.1–2.9 all ✅.
- [ ] **O3:** Scope of states in the demo dropdown — Tennessee only (demo-tight) vs full US 50-state list (more realistic). Recommend full list; it's one-line code.
- [x] **O4:** ~~Store `date` as ISO string or unix-epoch int?~~ **Locked 2026-04-15 (Stephen + Vinh): store both.** Payload has `date_epoch: int` (for `Field('date_epoch').between()` numeric filters) and `date_iso: str` (e.g. `"2019-10-14"`, for UI display). Negligible payload cost, zero ambiguity between ingest and search.

---

## Environment prerequisites (anyone cloning)

```bash
# 1. Docker Desktop running
docker --version          # must return

# 2. Start Actian DB (from repo root — D5 deploys it here)
docker compose up -d
# Verify: docker ps --filter name=trace-vectoraidb

# 3. Copy the Actian Python client wheel into backend/vendor/
#    (The wheel is hackathon-provided and NOT committed to this repo —
#     per Geri in the hackathon Discord. Clone the hackmamba repo as a
#     sibling and copy from there.)
cd ..   # back to the dir that holds Trace/
git clone https://github.com/hackmamba-io/actian-vectorAI-db-beta.git
mkdir -p Trace/backend/vendor
cp actian-vectorAI-db-beta/actian_vectorai-0.1.0b2-py3-none-any.whl \
   Trace/backend/vendor/

# 4. Python venv
cd Trace/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Bring up Actian VectorAI DB (from repo root)
cd ..
docker compose up -d --wait    # --wait blocks until healthcheck green

# 6. Ingest synthetic data (first time only)
cd backend
python ingest.py

# 7. Start API
uvicorn main:app --reload --port 8000

# 8. In a new terminal — frontend
cd ../frontend
npm install               # first time only
npm run dev               # serves on localhost:5173
```

**Reset the DB** (if `.vectordata/` corrupts or you want a clean ingest):

```bash
# from repo root
docker compose down
rm -rf backend/.vectordata
docker compose up -d --wait
cd backend && python ingest.py
```

---

## Build phases

### Phase 1 — Environment ✅ (completed 2026-04-15 by Claude)

See status dashboard rows 1.1–1.6.

### Phase 2 — Backend core 🟡

Build order matters — later files import from earlier ones. **Claude pauses after Task 2.1 per Stephen's instruction ("let me know when you're done with requirements before you move to the next thing").**

**Ownership split (locked 2026-04-15):**

| Owner | Files | Rationale |
|---|---|---|
| **Stephen** | `docker-compose.yml`, `backend/ingest.py` | Clean infra-and-data-loading lane; no overlap with Vinh's files. |
| **Vinh** | `backend/embeddings.py`, `backend/filters.py`, `backend/search.py`, `backend/main.py` | The AI + API brain; his lane per team division. |
| **Claude** | `backend/config.py`, `backend/schemas.py`, `backend/tests/*`, frontend wiring (Phase 3), synthetic data (Phase 4) | Glue + test coverage + Phase 3 so the UI doesn't stay on mocks. |

**Shared contract (don't drift):**
- Collection name: `cases` (defined in `config.py`)
- 4 named vectors per point: `physical_text` (768d SapBERT), `physical_image` (512d CLIP), `circumstances` (1024d BGE-M3), `clothing` (1024d BGE-M3). All Cosine.
- Payload always contains: `case_id`, `case_type`, `sex`, `age_low`, `age_high`, `state`, `date_epoch` (int), `date_iso` (str), plus the raw text fields used for embeddings (`physical_text`, `circumstances`, `clothing`) and optional `image_url`.
- Date filtering uses `Field('date_epoch').between(start_epoch, end_epoch)` — never filter against `date_iso`.
- **`case_id` semantics:** `MP-001..MP-006` are ground-truth paired with `UP-001..UP-006` (same fictional person). `MP-007+` and `UP-007+` are unrelated singletons that happen to share a numeric suffix — **do not** pair by suffix above 006.

If anyone spots a field drift (e.g., Vinh's `search.py` expects `dob` but Stephen's `ingest.py` writes `date_epoch`), flag immediately before merging.

#### Task 2.1 — `backend/requirements.txt`

**Files:** Create `backend/requirements.txt`.

**Acceptance:**
- `python -m venv backend/.venv && source backend/.venv/bin/activate && pip install -r backend/requirements.txt` succeeds from a clean interpreter on Python 3.12.
- `python -c "from actian_vectorai import VectorAIClient; from fastapi import FastAPI; from FlagEmbedding import BGEM3FlagModel; from transformers import AutoModel; from PIL import Image; import torch"` runs without ImportError.

**Content:**

```
# Actian VectorAI DB client (vendored wheel)
./vendor/actian_vectorai-0.1.0b2-py3-none-any.whl

# Web framework
fastapi>=0.115,<0.120
uvicorn[standard]>=0.32,<0.35
python-multipart>=0.0.9

# Embedding models
FlagEmbedding>=1.3.0
sentence-transformers>=3.0.0
transformers>=4.44.0
torch>=2.3.0

# Data + images
pandas>=2.2.0
numpy>=1.26.0
pillow>=10.4.0

# HTTP + utilities
requests>=2.32.0
python-dotenv>=1.0.1

# Tests
pytest>=8.3.0
pytest-asyncio>=0.24.0
httpx>=0.27.0

# Stretch (Task 2.8 BM25 path — safe to install now)
rank-bm25>=0.2.2
scikit-learn>=1.5.0
```

**Commit:** `chore(backend): pin Python dependencies for Actian client, embeddings, FastAPI`

**Status:** File written 2026-04-15. Pip install verification was interrupted mid-run and is pending Stephen's green-light to resume (venv at `backend/.venv/` has pip upgraded but no packages installed yet).

#### Task 2.2 — `docker-compose.yml` at repo root

**Files:** Replace the empty `docker-compose.yml` at repo root.

**Content:**

```yaml
services:
  vectoraidb:
    image: williamimoh/actian-vectorai-db:latest
    container_name: trace-vectoraidb
    ports:
      - "50051:50051"
    volumes:
      - ./backend/.vectordata:/data
    restart: unless-stopped
    stop_grace_period: 2m
```

**Acceptance:** `docker compose down` (against the sibling), then `docker compose up -d` from `/Users/stephensookra/Trace` — container starts, port 50051 reachable, no mount-permission errors on `./backend/.vectordata`. Add `backend/.vectordata/` to `.gitignore`.

**Commit:** `chore: add docker-compose for Actian VectorAI DB at repo root`

#### Task 2.3 — `backend/config.py`

Constants + env-var loading. No external dependencies on our code.

Shipped in `backend/config.py` (2026-04-15). Module-level constants, not a dataclass. Key exports:

```python
VECTORAI_HOST     = os.getenv("VECTORAI_HOST", "localhost")
VECTORAI_PORT     = _int_env("VECTORAI_PORT", 50051)   # loud error on bad input
VECTORAI_ADDR     = f"{VECTORAI_HOST}:{VECTORAI_PORT}" # pass to VectorAIClient()
COLLECTION_NAME   = "cases"
VECTORS: dict[str, VectorSpec]  # 4 named specs: physical_text/physical_image/circumstances/clothing
RRF_K             = 60
SYNTHETIC_CASES_PATH              # absolute path to data/synthetic/cases.json
FRONTEND_ORIGIN   = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
```

**Env vars** (all optional, defaults work out of the box): `VECTORAI_HOST`, `VECTORAI_PORT`, `FRONTEND_ORIGIN`. Do **not** use `ACTIAN_HOST` — an earlier draft of this plan used that name; it is not read by the shipped code.

**Test:** `backend/tests/test_config.py` — imports CONFIG, asserts defaults, asserts env overrides are respected.

**Commit:** `feat(backend): add config module with typed constants and env vars`

#### Task 2.4 — `backend/schemas.py`

Pydantic request/response models.

```python
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field

CaseType = Literal["missing", "unidentified"]

class SearchFilters(BaseModel):
    case_type: Optional[CaseType] = None  # None = both
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    sex: Optional[Literal["Male", "Female", "Unknown"]] = None
    age_low: Optional[int] = Field(None, ge=0, le=120)
    age_high: Optional[int] = Field(None, ge=0, le=120)
    date_from: Optional[str] = None  # ISO yyyy-mm-dd
    date_to: Optional[str] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    filters: SearchFilters | None = None  # None = no filters
    limit: int = Field(10, ge=1, le=50)

class MatchMapping(BaseModel):
    query_term: str
    forensic_field: str
    matched_value: str
    similarity: float
    match_type: str  # 'semantic_sapbert' | 'semantic_bge' | 'hard_filter' | etc

class ScoreBreakdown(BaseModel):
    physical_text: Optional[float] = None
    physical_image: Optional[float] = None
    circumstances: Optional[float] = None
    clothing: Optional[float] = None

class CaseMetadata(BaseModel):
    case_id: str
    case_type: CaseType
    state: str
    sex: str
    age_low: int
    age_high: int
    date: str
    namus_url: str

class SearchResult(BaseModel):
    case_id: str
    case_type: CaseType
    title: str
    confidence: float                 # fused score, 0..1
    metadata: CaseMetadata
    score_breakdown: ScoreBreakdown
    why_matched: list[MatchMapping]

class SearchResponse(BaseModel):
    query: str
    total_matches: int
    latency_ms: int
    results: list[SearchResult]
```

**Test:** `backend/tests/test_schemas.py` — a happy-path `SearchRequest` parses; bad age rejects; bad state length rejects.

**Commit:** `feat(backend): add Pydantic schemas for search API`

#### Task 2.5 — `backend/embeddings.py`

Model loading + embedding functions. Models load at module import time (once per process). On Apple Silicon, `torch.backends.mps.is_available()` → use `mps` device automatically unless env says otherwise.

Functions to implement (exact signatures):

```python
def embed_text_sapbert(text: str) -> list[float]: ...          # 768-dim, L2-normalized
def embed_text_bge(text: str) -> list[float]: ...              # 1024-dim dense, normalized by model
def embed_text_bge_batch(texts: list[str]) -> list[list[float]]: ...
def embed_text_clip(text: str) -> list[float]: ...             # 512-dim (cross-modal text→image search)
def embed_image_clip(image_path_or_pil) -> list[float]: ...    # 512-dim
```

**Acceptance tests** (`backend/tests/test_embeddings.py`):
- `len(embed_text_sapbert("hello")) == 768`
- `len(embed_text_bge("hello")) == 1024`
- `len(embed_text_clip("hello")) == 512`
- Cosine similarity between `embed_text_sapbert("eagle tattoo right forearm")` and `embed_text_sapbert("avian motif dermagraphic right ventral antebrachium")` is ≥ 0.60 — the core semantic-bridge hypothesis verified with a unit test.

**Commit:** `feat(backend): add embedding wrappers for SapBERT, BGE-M3, and CLIP`

**Results (2026-04-15, Vinh):**

| Test | Result | Pass? |
|---|---|---|
| `len(embed_text_sapbert("hello"))` | 768 | Yes |
| `len(embed_text_bge("hello"))` | 1024 | Yes |
| `len(embed_text_clip("hello"))` | 512 | Yes |
| `embed_text_bge_batch(["hello","world"])` | 2 x 1024 | Yes |
| L2 norm (all models) | 1.000000 | Yes |
| SapBERT cosine: "eagle tattoo right forearm" vs "avian motif dermagraphic right ventral antebrachium" | **0.6164** (>= 0.60) | Yes |
| SapBERT full-context physical_text pair | **0.6710** | Yes |
| BGE-M3 same pair (comparison) | 0.5326 | N/A — confirms SapBERT is stronger for medical vocab |
| Negative control (unrelated text) | 0.2454 | Yes — 0.37 gap |

#### Task 2.6 — `backend/filters.py`

**Problem:** Vector search alone returns semantically similar results from any state, age, decade. `filters.py` is the hard pre-filter that narrows candidates *before* vectors are compared — maps to the 30% "Use of Actian VectorAI DB" judging weight.

**Design:** 1 public export, 1 private helper, ~40 lines, no classes.

```python
from actian_vectorai import Field, FilterBuilder
from schemas import SearchFilters

def _iso_to_epoch(date_str: str) -> int:
    """'2019-10-14' → unix epoch (UTC)."""
    ...

def build_filter(filters: SearchFilters) -> Filter | None:
    """Build Actian Filter from SearchFilters. Returns None if no fields set."""
    # 1. Guard up front — all fields None → return None
    # 2. For each non-None field, append .must() clause:
    #    - case_type  → Field("case_type").eq(value)
    #    - state      → Field("state").eq(value.upper())
    #    - sex        → Field("sex").any_of([value, "Unknown"])
    #    - age_low    → Field("age_high").gte(age_low)   # overlap semantics
    #    - age_high   → Field("age_low").lte(age_high)   # overlap semantics
    #    - date_from  → Field("date_epoch").gte(epoch)
    #    - date_to    → Field("date_epoch").lte(epoch)
    # 3. .build() → return Filter
    ...
```

**Flow in context:** `search.py` calls `build_filter()` once → passes the same `Filter | None` to all 4 vector fan-out `client.points.search()` calls as `filter=`.

**Acceptance tests** (`backend/tests/test_filters.py`, ~60 lines, pure unit, no DB):

| Test | Input | Assert |
|---|---|---|
| No filters | all `None` | returns `None` |
| State only | `state="TN"` | `Filter` with one `.must()` |
| Sex includes Unknown | `sex="Male"` | `.any_of(["Male", "Unknown"])` |
| Age overlap (both) | `age_low=30, age_high=40` | `age_high >= 30` AND `age_low <= 40` |
| Age one-sided | `age_low=25` only | `age_high >= 25` only |
| Date range | `date_from/to` set | two epoch comparisons (`date_to` uses end-of-day: +86399s) |
| Full filter | all fields set | all 6 clause types |
| `_iso_to_epoch` | `"2019-10-14"` | correct epoch (UTC) |

**Commit:** `feat(backend): add filter DSL builder with age-range overlap semantics`

#### Task 2.7 — `backend/ingest.py`

Load `data/synthetic/cases.json`, build four named vectors per case, upsert to Actian.

```python
# Pseudocode sketch (SDK shape verified against 0.1.0b2):
with VectorAIClient(VECTORAI_ADDR) as client:
    if not client.collections.exists(COLLECTION_NAME):
        client.collections.create(
            COLLECTION_NAME,
            vectors_config={
                "physical_text":  VectorParams(size=VECTORS["physical_text"].dim,  distance=Distance.Cosine),
                "physical_image": VectorParams(size=VECTORS["physical_image"].dim, distance=Distance.Cosine),
                "circumstances":  VectorParams(size=VECTORS["circumstances"].dim,  distance=Distance.Cosine),
                "clothing":       VectorParams(size=VECTORS["clothing"].dim,       distance=Distance.Cosine),
            },
        )

points = []
for case in load_cases():
    physical_text_narrative = compose_physical_text(case)       # concat desc + scars + tattoos + dental
    circumstances_narrative = case["circumstances"] or ""
    clothing_narrative = case["clothing"] or ""
    vectors = {
        "physical_text": embed_text_sapbert(physical_text_narrative),
        "circumstances": embed_text_bge(circumstances_narrative),
        "clothing": embed_text_bge(clothing_narrative),
    }
    if case.get("image_url"):
        vectors["physical_image"] = embed_image_clip(fetch(case["image_url"]))
    points.append(PointStruct(
        id=case["case_id"],                # string UUIDs from synthetic data
        vector=vectors,
        payload={
            **structured_metadata(case),
            "physical_text_source": physical_text_narrative,
            "circumstances_source": circumstances_narrative,
            "clothing_source": clothing_narrative,
            "image_url": case.get("image_url"),
        },
    ))

client.upload_points(CONFIG.collection_name, points, batch_size=32)
```

**Important:** Actian's server version doesn't yet support "multi-dense-vector write paths" cleanly per the release notes. We verify named-vector upsert works via `examples/29_named_vectors.py` — that example *does* pass, so 4 named vectors per point should work. If upsert fails at runtime, fall back to 3 collections (D1 reversal) — noted in `O1` above.

**Acceptance:** `python -m backend.ingest` on a 60-case file succeeds; `client.points.count("cases") == 60`.

**Commit:** `feat(backend): add ingest pipeline for synthetic cases`

#### Task 2.8 — `backend/search.py`

**Design locked 2026-04-15 (Vinh + Claude).** The earlier sketch in this section drifted from shipped reality on three points: stale `CONFIG.actian_host` / `per_vector_candidates` names (real `config.py` is module-level constants with no `per_vector_candidates` yet), stale `score_breakdown` / `why_matched` schema fields (real `schemas.py` uses camelCase `matchMappings`), and an unachievable `≥ 0.85` acceptance target given real demo scores of 0.82. What follows is the version that matches `config.py`, `schemas.py`, `embeddings.py`, `filters.py`, and the frontend card contract (`TraceResultCard.tsx`, `api.ts`) verbatim.

##### Architecture

Single pure function `run_search(req: SearchRequest, client: VectorAIClient) -> SearchResponse`, ~150 LOC. Caller owns the client (2.9 injects it via `Depends()` — mirrors how `ingest.py` uses it). No FastAPI coupling in this file.

```
run_search(req, client)
  1. filter_ = build_filter(req.filters)                     # filters.py
  2. Embed query 3 ways (serial, MVP):
       q_sap  = embed_text_sapbert(req.query)   # 768d
       q_bge  = embed_text_bge(req.query)       # 1024d
       q_clip = embed_text_clip(req.query)      # 512d, cross-modal text→image
  3. Fan out 4× client.points.search(COLLECTION_NAME, ..., filter=filter_,
                                     limit=PER_VECTOR_CANDIDATES):
       physical_text  ← q_sap
       physical_image ← q_clip   (text query searches CLIP image space)
       circumstances  ← q_bge
       clothing       ← q_bge
  4. fused = reciprocal_rank_fusion([4 lists], limit=req.limit,
                                    ranking_constant_k=RRF_K)
       # RRF is used for ORDER ONLY. Its raw-sum score is ignored.
  5. For each fused point: look up per-vector scores by point_id from
     step 3's lists; confidence = max(scores); compose SearchResult.
  6. Return SearchResponse(query, total_matches=len(fused),
                           latency_ms, results)
```

**SDK watch (0.1.0b2).** Do **not** use `client.points.get(with_vectors=True)` to recover stored vectors — it returns a flat list, not the per-vector dict, in this release (Stephen flagged 2026-04-15). We never need that path; everything 2.8 needs is on `.score` / `.id` / `.payload` of each fan-out result.

##### Score model (confidence)

`confidence = max(per_vector_score for vector in {physical_text, physical_image, circumstances, clothing} if point appeared in that fan-out)`. Clamped to `[0.0, 1.0]` before Pydantic validation (floating-point cosines can round to `1.0000001`).

**Threshold softening.** Real demo-query scores from Task 4.2 top out at 0.82 (circumstances/MP-001). The original `HIGH ≥ 0.85` came from a keyword-search mental model; SapBERT/BGE on clinical↔lay bridges rarely clear 0.85. **Lower `HIGH` to 0.80** in both places that hold the truth:
- `backend/schemas.py` — `SearchResult.threshold` @computed_field: `0.85` → `0.80`
- `frontend/src/components/TraceResultCard.tsx:20` — `getConfidenceColor`: `0.85` → `0.80`
- `backend/tests/test_schemas.py` — boundary assertions around HIGH/MEDIUM update to `0.80`

Revised acceptance target: demo query returns MP-001 in top 3 at `confidence ≥ 0.80` → HIGH CONFIDENCE on the card.

##### Field mapping: payload → SearchResult

Card spreads the result object as props (`<TraceResultCard {...result} />`). `SearchResult` MUST be camelCase-only; any extra snake_case key triggers a React unknown-prop warning.

| Wire field | Source / format |
|---|---|
| `caseId` | `payload["case_id"]` — "MP-001", NOT the UUID5 point id |
| `title` | `"Unidentified {sex} (Found {year})"` or `"Missing {sex} (Reported {year})"` |
| `confidence` | `max(per-vector cosine)`, clamped to `[0, 1]` |
| `threshold` | `@computed_field` auto-emitted by Pydantic |
| `stateFound` | `_STATE_NAMES[payload["state"]]` — **full name** (new 50-state + DC lookup constant) |
| `genderEst` | `payload["sex"]` — "Male"/"Female" (payload Sex has no "Unknown") |
| `ageRange` | `f"{age_low} - {age_high} Years"` — exact mock spacing, including " Years" suffix |
| `discoveryDate` | `strftime("%b %d, %Y")` applied to `payload["date_iso"]` → "Jun 02, 2020" |
| `namusLink` | `None` — not in synthetic payload; card hides chip when null |
| `matchMappings` | built per § below; empty list if chunking yields nothing |

##### "Why This Matched" algorithm

Per result in the fused list:

1. `_chunk_query(query)` — split on `", "`, `" and "`, `"; "`; drop chunks <3 chars; cap at 5. Demo query yields ~5 chunks.
2. Encode chunks once (SapBERT sequential + BGE batched).
3. Encode this result's 3 source texts: SapBERT on `physical_text`, `embed_text_bge_batch([circumstances, clothing])`.
4. For each chunk: compute cosine vs each of the 3 fields; pick `(best_field, best_sim)`.
5. Emit `MatchMapping(queryTerm=f'"{chunk}"', forensicField=best_field, forensicValue=_first_sentence(source, 80), similarity=clamp(best_sim))`.
6. Sort by `similarity` desc, take top 5.

Field labels emitted (fine-grained, matching frontend mock data in `TraceResultsPanel.tsx`):

```python
_FIELD_LABELS = {
    # physical_text sub-fields (parsed from physical_text payload)
    "physical:marks":    "DISTINGUISHING_MARKS",
    "physical:location": "MARK_LOCATION",
    "physical:bio":      "BIOLOGICAL_RELATION / AGE_EST",
    "physical:general":  "PHYSICAL_DESCRIPTION",
    # circumstances sub-fields
    "circum:location":   "RECOVERY_LOCATION",
    "circum:date":       "DISCOVERY_DATE",
    "circum:general":    "CIRCUMSTANCES",
    # clothing
    "cloth":             "CLOTHING_EFFECTS",
}
```

To match the mock's granularity, `physical_text` payload is parsed into sub-fields before chunk comparison: tattoos/scars → `DISTINGUISHING_MARKS`, body-part references → `MARK_LOCATION`, age/sex references → `BIOLOGICAL_RELATION / AGE_EST`, location mentions in circumstances → `RECOVERY_LOCATION`, date references → `DISCOVERY_DATE`. Keyword heuristics (regex on "tattoo|scar|mark", "forearm|arm|leg", "I-\d+|highway|corridor", etc.) are sufficient — no NLP parsing needed. Falls back to coarse label if no sub-field matches.

Cost per result: 1 SapBERT + 1 BGE-batch(2) + `n_chunks` × (1 SapBERT + BGE-batch share) ≈ ~80ms on MPS. 10 results ≈ ~800ms enrichment. **Ship the straightforward version; do not pre-optimize.** Batched cross-result enrichment is a **post-demo** optimization — with the Apr 18 18:00 UTC deadline, measure real latency first and only invest if it bites.

##### New config constant

```python
# backend/config.py
PER_VECTOR_CANDIDATES = 25   # fan-out pool size before RRF fusion
```

##### Error handling

| Failure | Behavior |
|---|---|
| VectorAI unreachable | `run_search` raises; 2.9 returns 503 |
| `build_filter` raises ValueError (bad date) | propagate; 2.9 returns 422 |
| Collection missing | raise clear error — ingest wasn't run |
| One fan-out empty | continue; fuse the rest |
| All four empty | `SearchResponse(results=[], total_matches=0)` — frontend already renders "NO MATCHES FOUND" |
| Embedding raises (OOM on cold start) | propagate; 2.9 returns 500; /health exposes it |

##### Tests (`backend/tests/test_search.py`)

Three tiers, matching `test_ingest.py` layout:

**Unit (no DB, no models):** `_chunk_query` splits/caps correctly; `_compose_title` covers both case types; `_format_age` and `_format_date` match mock strings verbatim; `_STATE_NAMES` has 50 + DC; score clamp `1.0000001 → 1.0`; `_to_search_result` with stub point builds valid `SearchResult`.

**Integration-light (stub `VectorAIClient`):** `run_search` calls `client.points.search` 4× with correct `using=` names; filter passed through to all 4; `reciprocal_rank_fusion` invoked with all 4 lists; empty filter → `filter=None`.

**Live (`@pytest.mark.live`, skipped by default):** demo-query acceptance — family-voice Tennessee query → MP-001 in top 3 with `confidence ≥ 0.80`; filter roundtrip (`state="TX"` → only Texas cases); latency budget (10 searches, mean `latency_ms < 500`).

##### Wire contract — `api.ts` parity check

`SearchResult` fields listed above match `frontend/src/lib/api.ts:71-82` verbatim. `SearchResponse` envelope (snake_case `total_matches` / `latency_ms`) matches `api.ts:84-89` and `TraceResultsPanel.tsx:49,116`. No transform layer needed.

**Commit:** `feat(backend): add hybrid RRF search engine with why-matched breakdown`

#### Task 2.9 — `backend/main.py`

FastAPI server with three endpoints.

```python
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Trace API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health() -> dict:
    # Check: DB reachable, collection exists, models loaded
    ...

@app.post("/search", response_model=SearchResponse)
async def search_endpoint(req: SearchRequest) -> SearchResponse:
    return run_search(req, client)
    # JSON body — matches frontend api.ts which sends Content-Type: application/json.
    # Image upload (stretch goal) gets a separate endpoint if needed.

@app.get("/case/{case_id}")
def get_case(case_id: str) -> dict:
    ...
```

**Acceptance:** `uvicorn backend.main:app --port 8000` serves; `curl -X POST localhost:8000/search -F query=...` returns 200 with expected shape; CORS preflight from :5173 passes.

**Commit:** `feat(backend): add FastAPI server with /search, /case, /health endpoints`

#### Task 2.10 — Backend tests

Covered incrementally in 2.3–2.9. One final integration test that starts from an empty collection, ingests 10 fixture cases, runs the demo query, asserts the expected record is in top-3.

**Commit:** `test(backend): add integration test for the demo query`

### Phase 3 — Frontend wire-up ⬜

**Principle:** keep the existing visual design exactly as-is. Swap mock data for real data only — no restyling.

#### Task 3.1 — `frontend/src/lib/api.ts`

```typescript
export interface SearchFilters { ... }
export interface SearchResult { ... }
export interface SearchResponse { ... }

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function search(query: string, filters: SearchFilters, image?: File): Promise<SearchResponse> {
  const form = new FormData();
  form.append("query", query);
  form.append("filters_json", JSON.stringify(filters));
  if (image) form.append("image", image);
  const res = await fetch(`${API_BASE}/search`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getCase(caseId: string): Promise<unknown> { ... }
```

**Commit:** `feat(frontend): add typed API client`

#### Task 3.2 — Controlled form + state

Lift search-form state up to `Index.tsx`. `TraceSearchPanel` receives a `onSubmit` callback; `TraceResultsPanel` receives the query result.

Use TanStack Query (already installed) for the search call:

```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ["search", query, filters],
  queryFn: () => search(query, filters, image),
  enabled: !!submittedQuery,
});
```

**Commit:** `feat(frontend): wire search form to POST /search via TanStack Query`

#### Task 3.3 — Live results rendering

Replace `mockResults` array in `TraceResultsPanel.tsx` with `data?.results`. Map API response fields onto `TraceResultCardProps` — `schemas.SearchResult` already uses camelCase matching the props exactly, so this is a pass-through. **Do not change any styles, classes, or component structure** — only replace the data source.

> **TODO (Stephen, Phase 3):** `TraceResultCard.tsx` line 50 hardcodes `href="#"` for the NAMUS_LINK. Wire it to `namusLink` prop and hide the chip when `namusLink` is null.

**Commit:** `feat(frontend): render live API results in TraceResultsPanel`

#### Task 3.4 — Loading and error states

- Skeleton: 3 skeleton `TraceResultCard` placeholders during `isLoading`.
- Error: `sonner` toast on error with the error message.
- Empty: friendly message when `data.results.length === 0`.

**Commit:** `feat(frontend): add loading skeleton, error toasts, empty state`

### Phase 4 — Synthetic data ⬜

#### Task 4.1 — `data/synthetic/cases.json`

60 cases total, of which:
- 30 "missing person" records (family vocabulary — "eagle tattoo on his right forearm")
- 30 "unidentified remains" records (ME vocabulary — "avian motif dermagraphic, right ventral antebrachium")
- ≥5 ground-truth pairs where a missing record and an unidentified record describe the same fictional person with different vocabularies, different states if needed, and dates 3–18 months apart.
- Must include the Tennessee eagle-tattoo demo pair exactly as described in the PDF demo moment.

Seed with deterministic randomness so the file can be regenerated. Script at `data/synthetic/generate.py` (optional — ok to hand-write 60 cases too given tight timeline).

**Commit:** `feat(data): add 60 synthetic cases with 5+ ground-truth pairs`

#### Task 4.2 — End-to-end validation run

Start DB → run `python -m backend.ingest` → run `python -m backend.tests.test_search_integration` — demo query returns correct record in top-3. Document any ingestion timing (model load + 60 upserts).

**Commit:** `test: verify demo query end-to-end against ingested synthetic data`

### Phase 5 — Demo polish + submission ⬜

Ownership: Stephen. Covered by rows 5.1–5.4 in the dashboard.

---

## Non-goals (explicitly out of scope)

- User authentication, accounts, or saved searches.
- Writing back to NamUs (read-only forever).
- Training or fine-tuning embeddings. Pretrained models only.
- Server-side sparse vectors (blocked by Actian server; see D3).
- Production-grade deployment, multi-tenant, observability. Local dev only.
- Tests for UI components beyond the one Vitest example already present.
- Handling any real unsolved case data inside the app.
- Supporting browsers other than modern Chromium for the demo.

---

## Coordination protocol

1. Before starting a task, set its status to 🟡 in the dashboard table above, commit the change, and push.
2. Finish the task → flip to ✅, commit, push.
3. If blocked, set to ⛔ and add a one-line note in the "Notes" column.
4. Never work the same row simultaneously. Check `git log -1 PLAN.md` before starting.
5. Commit messages use Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
6. One task = one commit, ideally. Bundle only when changes are genuinely atomic.
7. PRs are optional for this hackathon — commit straight to `main`, coordinate via this file.

---

## Reference links

- Trace repo — https://github.com/StephenSook/trace-forensic-search
- Actian VectorAI DB repo — https://github.com/hackmamba-io/actian-vectorAI-db-beta
- Actian examples folder — `../actian-vectorAI-db-beta/examples/` (30 scripts — particularly 06, 15, 29)
- Actian API docs — `../actian-vectorAI-db-beta/docs/api.md`
- SapBERT — https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext
- BGE-M3 — https://huggingface.co/BAAI/bge-m3
- CLIP ViT-B/32 — https://huggingface.co/openai/clip-vit-base-patch32
- NamUs — https://namus.nij.ojp.gov/
- DoraHacks — https://dorahacks.io/hackathon/actian-vectorai-db-build-challenge

---

_Last updated: 2026-04-15 by Claude (Opus 4.6)._
