# Trace

**Semantic search for missing persons and unidentified remains.**
A language bridge between grieving families and forensic records — built on Actian VectorAI DB.

---

## The Problem

600,000 people are reported missing in the United States every year. 40,000 sets of unidentified human remains exist in the national system. The data to connect them already exists. The technology to bridge them does not.

NamUs — the National Missing and Unidentified Persons System — is the federal database where both missing persons reports and unidentified remains cases live. But it runs on keyword search. And a grieving family and a medical examiner describing the same person use completely different languages.

A mother searching for her son describes an eagle tattoo on his right forearm. The medical examiner's record reads "avian motif dermagraphic, right ventral antebrachium." A family says he had a birthmark on his left shoulder. The record reads "pigmented lesion, left dorsal region." These two descriptions of the same person share almost no vocabulary — so they never meet.

Not because the match doesn't exist. Because there is no semantic bridge.

Trace is that bridge.

---

## The Demo Moment

A user types, in plain English:

> *"My brother went missing in 2019 in Tennessee. He was 34, about 6 feet tall, had a distinctive tattoo of an eagle on his right forearm, and was last seen near a highway."*

Trace returns the top hit:

> **Case UP-001 — Unidentified Male, recovered 2020** · confidence **HIGH (0.81)**
> *"Male, mid-30s, avian motif dermagraphic, right ventral antebrachium, recovered near I-40 corridor. Estimated stature 178cm."*

Every "Why This Matched" row shares **zero characters** with the query:

| Family said | Record said | Bridge |
|---|---|---|
| eagle tattoo | avian motif dermagraphic | SapBERT (biomedical) |
| right forearm | right ventral antebrachium | SapBERT (anatomical) |
| near a highway | I-40 corridor | BGE-M3 (circumstance) |
| about 6 feet | stature 178cm | semantic + numeric |
| 2019, Tennessee | 2020, TN | hard filter + temporal window |

Under keyword search, this match never happens. Under Trace, it's the top hit.

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
2. **Multi-vector retrieval** — query embedded by BGE-M3 (dense + sparse) and SapBERT; each named space searched independently. CLIP runs if a photo is uploaded.
3. **Hybrid fusion** — results merged via Reciprocal Rank Fusion (k=60). No hyperparameter tuning; consistently beats linear weighting.
4. **Ranked output** — top candidates with per-dimension score breakdown, a side-by-side terminology translation, and a direct NamUs case link.

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

# 2. Backend — Python 3.12 venv + deps
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# 3. Start Actian VectorAI DB (from repo root)
cd .. && docker compose up -d --wait

# 4. Ingest synthetic data, then start the API
cd backend && python ingest.py
uvicorn main:app --reload --port 8000

# 5. In a new terminal — frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:8080**. Full setup and architecture notes live in [`PLAN.md`](./PLAN.md).

---

## Stack

- **Vector DB** — Actian VectorAI DB 0.1.0b2 (gRPC, local)
- **Embeddings** — SapBERT, BGE-M3, CLIP ViT-B/32 (all local, MPS/CUDA/CPU auto-detected)
- **Backend** — FastAPI + Pydantic v2, Python 3.12
- **Frontend** — React 18 + Vite + TanStack Query + Tailwind
- **Tests** — pytest (backend), Vitest (frontend)

---

## Built For

Actian VectorAI DB Build Challenge · April 13–18, 2026

## Team

Stephen Sookra · Vinh Le

## License

MIT © 2026 Stephen Sookra, Vinh Le
