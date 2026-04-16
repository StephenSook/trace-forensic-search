# Trace

Semantic search for missing persons and unidentified remains.

A language bridge between grieving families and forensic records — built on Actian VectorAI DB.

---

## The Problem

600,000 people are reported missing in the United States every year. 40,000 sets of unidentified human remains exist in the national system. The data to connect them already exists. The technology to bridge them does not.

NamUs — the National Missing and Unidentified Persons System — is the federal database where both missing persons reports and unidentified remains cases live. But it runs on keyword search. And a grieving family and a medical examiner describing the same person use completely different languages.

A mother searching for her son describes an eagle tattoo on his right forearm. The medical examiner's record reads "avian motif dermagraphic, right ventral antebrachium." A family says he had a birthmark on his left shoulder. The record reads "pigmented lesion, left dorsal region." These two descriptions of the same person share almost no vocabulary — so they never meet.

Not because the match doesn't exist. Because there is no semantic bridge.

Trace is that bridge.

---

## What It Does

Trace lets an investigator, advocate, or family member describe a missing person in plain language and semantically matches that description against unidentified remains records. It bridges clinical forensic terminology with layperson narrative using vector embeddings, named vectors, and hybrid fusion search — all running locally with no cloud dependency.

---

## How It Works

Trace stores each case record across three independent named vector spaces — physical description, circumstances of disappearance or recovery, and clothing and personal effects. A fourth vector space handles tattoo and identifying photos via cross-modal image search. Hard metadata filters on sex, age range, state, and date window are applied before any vector computation. Dense semantic search and sparse keyword search are then fused using Reciprocal Rank Fusion, and results are returned with a score breakdown and a side-by-side terminology translation showing exactly why each record matched.

---

## Quick Start

```bash
# 1. Vendor the Actian wheel (copy from the hackmamba challenge repo — not in git)
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

Open http://localhost:5173. Full setup and architecture notes live in `PLAN.md`.

---

## Why Local-First

Forensic databases contain restricted personally identifiable information — DNA profiles, dental records, and unredacted case circumstances. Sending this data to cloud APIs violates the regulatory environment these tools operate in. Trace runs entirely offline: local Docker container, local embedding models, zero external API calls after setup.

---

## Built For

Actian VectorAI DB Build Challenge · April 13–18, 2026

---

## Team

Stephen Sookra
Vinh Le

---

## License

MIT © 2026 Stephen Sookra, Vinh Le
