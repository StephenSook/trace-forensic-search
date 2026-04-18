# Trace

**Semantic search for missing persons and unidentified remains.**
A language bridge between grieving families and forensic records — built on Actian VectorAI DB.

**Live preview:** https://trace-forensic-search-ssookra-7703s-projects.vercel.app (frontend only — backend runs locally)

---

## The Problem

600,000 people are reported missing in the United States every year. 40,000 sets of unidentified human remains exist in the national system. The data to connect them already exists. The technology to bridge them does not.

NamUs — the National Missing and Unidentified Persons System — is the federal database where both missing persons reports and unidentified remains cases live. But it runs on keyword search. And a grieving family and a medical examiner describing the same person use completely different languages.

A mother searching for her son describes an *eagle tattoo on his right forearm*. The medical examiner's record reads *"avian motif dermagraphic, right ventral antebrachium."* Same person. Zero shared vocabulary. Keyword search never makes the connection.

Trace is the semantic bridge.

---

## The Demo Moment

A user types, in plain English:

> *"My brother went missing in 2019 in Tennessee. He was 34, about 6 feet tall, had a distinctive tattoo of an eagle on his right forearm, and was last seen near a highway."*

With filters set to **Unidentified Remains** and **Tennessee**, Trace returns:

> **Case UP-001 — Unidentified Male, recovered 2020** · confidence **HIGH (0.79)**

Every "Why This Matched" row shares **zero words** with the query:

| Family said | Record said | Bridge |
|---|---|---|
| eagle tattoo | avian motif dermagraphic | SapBERT (biomedical) |
| right forearm | right ventral antebrachium | SapBERT (anatomical) |
| near a highway | beside the highway, I-40 | BGE-M3 (circumstance) |
| He was 34 | mid-30s | SapBERT (age estimation) |
| 2019, Tennessee | 2020, TN | hard filter + temporal proximity |

Under keyword search, this match never happens. Under Trace, it's the top hit.

**Then** — upload a photo of an eagle tattoo. Trace encodes it with CLIP and searches across the image vector space. Same case, confidence 0.51 (MEDIUM). Text bridged the vocabulary gap. Images bridge the modality gap.

---

## How It Works

Each case record lives across **four independent named vector spaces** in Actian VectorAI DB — not one embedding of the whole record, which would dilute the signal:

| Named vector | Dim | Model | Encodes |
|---|---|---|---|
| `physical_text` | 768 | SapBERT | physical description, scars, marks, tattoos, dental |
| `circumstances` | 1024 | BGE-M3 | narrative of disappearance or recovery |
| `clothing` | 1024 | BGE-M3 | apparel, jewelry, personal effects |
| `physical_image` | 512 | CLIP ViT-B/32 | tattoo or identifying photos (cross-modal) |

A query runs through a four-stage pipeline:

1. **Hard filter** — sex, age-range overlap, state, date window, case_type — applied *before* any vector math, using Actian's native filter DSL.
2. **Multi-vector retrieval** — query embedded by SapBERT, BGE-M3, and CLIP; each named space searched independently. If a photo is uploaded, CLIP encodes it for cross-modal image→text matching.
3. **Hybrid fusion** — results merged via Reciprocal Rank Fusion (k=60). No hyperparameter tuning; consistently beats linear weighting.
4. **Ranked output** — top candidates with clause-level confidence scoring, a side-by-side "Why This Matched" terminology translation, and full case detail view.

---

## What Makes This VectorAI-Native

Trace uses Actian VectorAI DB as a first-class primitive, not a generic vector store:

- **Named vectors** — four independent embedding spaces on a single collection, queried per-space with `points.search(vector=, using=)`.
- **Hard pre-filter DSL** — `Filter`, `FieldCondition`, `MatchAny`, and `Range` composed before vector computation, so recall budget is never spent on wrong-sex or wrong-state candidates.
- **Deterministic point IDs** — UUID5 over `case_id` so re-ingest is idempotent.
- **Local gRPC on port 50051** — no cloud, no network calls, no PII leaving the box.

---

## Why Local-First

Forensic databases contain restricted personally identifiable information — DNA profiles, dental records, and unredacted case circumstances. Sending this data to cloud APIs violates the regulatory environment these tools operate in. Trace runs entirely offline: local Docker container, local embedding models, zero external API calls after setup.

---

## Quick Start

```bash
# 1. Vendor the Actian wheel (copy from the hackathon challenge repo — not in git)
mkdir -p backend/vendor
cp /path/to/actian-vectorAI-db-beta/actian_vectorai-0.1.0b2-py3-none-any.whl backend/vendor/

# 2. Start Actian VectorAI DB
docker compose up -d --wait

# 3. Backend — Python 3.12 venv + deps
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# 4. Ingest synthetic data, then start the API
python ingest.py
uvicorn main:app --reload --port 8000

# 5. In a new terminal — frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**. Full setup and architecture notes live in [`PLAN.md`](./PLAN.md).

---

## Stack

- **Vector DB** — Actian VectorAI DB 0.1.0b2 (gRPC, local)
- **Embeddings** — SapBERT, BGE-M3, CLIP ViT-B/32 (all local, MPS/CUDA/CPU auto-detected)
- **Backend** — FastAPI + Pydantic v2, Python 3.12
- **Frontend** — React 18 + Vite + TanStack Query + Tailwind
- **Tests** — pytest (205 backend tests), Vitest (frontend)

---

## Built For

Actian VectorAI DB Build Challenge · April 13–25, 2026

## Team

Stephen Sookra · Vinh Le

## License

MIT © 2026 Stephen Sookra, Vinh Le
