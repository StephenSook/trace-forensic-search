# Trace — DoraHacks BUIDL Submission Draft

Source of truth for the DoraHacks submission. Copy-paste targets once Stephen confirms exact form fields from screenshots.

---

## Canonical Hackathon Facts

- **URL:** https://dorahacks.io/hackathon/2097
- **Deadline:** April 25, 2026 — **18:00 UTC** (timeline block is authoritative; banner shows "12:00" in an ambiguous timezone — verify from logged-in view)
- **Hard requirements:** GitHub/GitLab/Bitbucket link · Demo video
- **Team cap:** 4
- **Rubric:** Actian usage 30% · Real-world impact 25% · Technical execution 25% · Demo & presentation 20% · Bonus for local/ARM/offline
- **Prizes:** 3 mo Claude Max 5x per person (1st) · 1 mo Claude Max 5x per person (2nd) · 1 mo Claude Pro per person (3rd)

---

## Submission Content

### Project name

`Trace`

### Tagline (≤100 chars)

> A semantic bridge between grieving families and forensic records, built on Actian VectorAI DB.

*(99 chars)*

### Alt tagline (≤60 chars, if DoraHacks splits name + tagline tight)

> Semantic search for missing persons and unidentified remains.

*(60 chars)*

### Short description (~200–400 chars)

> Trace closes the vocabulary gap between how families describe missing loved ones and how medical examiners write forensic records. A family's "eagle tattoo on his right forearm" and a record's "avian motif dermagraphic, right ventral antebrachium" share zero characters — keyword search never connects them. Trace does, using four named vector spaces in Actian VectorAI DB and reciprocal rank fusion, entirely on-device.

### Long description / full writeup

> **The problem.** 600,000 people are reported missing in the United States every year. 40,000 sets of unidentified human remains sit in the national system. Both live in NamUs — the federal Missing and Unidentified Persons System — but NamUs runs on keyword search. A grieving family and a medical examiner describing the same person use completely different vocabularies. A mother searches for an *"eagle tattoo on his right forearm"*; the record reads *"avian motif dermagraphic, right ventral antebrachium."* Same person. Zero shared words. The match never happens.
>
> **What Trace does.** A user types a missing-person description in plain English. Trace semantically matches it against unidentified-remains records and returns ranked candidates with a per-dimension score breakdown and a side-by-side translation panel showing exactly *why* each record matched. Every technical decision traces back to making one demo query work: *"My brother went missing in 2019 in Tennessee. He was 34, about 6 feet tall, had a distinctive tattoo of an eagle on his right forearm, and was last seen near a highway."* Top result: confidence 0.79 (HIGH), warm-path under a second. Upload a photo of an eagle tattoo and the same case surfaces again via CLIP cross-modal matching — text bridges the vocabulary gap, images bridge the modality gap.
>
> **How we use Actian VectorAI DB.** Not as a generic vector store — as a first-class primitive.
>
> 1. **Four named vector spaces on one collection.** Physical description (768d SapBERT — biomedical model, the only one that treats "eagle tattoo" and "avian motif dermagraphic" as the same concept), circumstances (1024d BGE-M3), clothing (1024d BGE-M3), and tattoo/photo image (512d CLIP ViT-B/32). Each queried independently via `points.search(vector=, using=)`. Embedding the whole case as one vector was deliberately rejected — it dilutes the signal.
> 2. **Hard pre-filter DSL.** Sex, age-range overlap, state, date window, and case type applied *before* any vector computation using Actian's `FilterBuilder` with `Field.eq()`, `Field.any_of()`, and `Field.gte()`/`Field.lte()` range operators. Recall budget is never spent on wrong-state or wrong-sex candidates.
> 3. **Reciprocal Rank Fusion.** Dense and sparse retrievals fused at k=60. No hyperparameter tuning; consistently beats weighted-sum. Interpretable — we can show a medical examiner exactly why a record ranked where it did.
> 4. **Deterministic UUID5 point IDs** keyed on case_id so re-ingest is idempotent.
>
> **Local-first by requirement, not aesthetic.** Forensic data contains restricted PII — DNA profiles, dental records, unredacted case circumstances. Cloud APIs are a regulatory non-starter for the people we built this for. Actian runs in one local Docker container on gRPC port 50051; the embedding models run natively on Apple Silicon via MPS (CUDA and CPU fallbacks included); zero external calls after setup. The whole stack fits on a laptop.
>
> **Stack.** Actian VectorAI DB 0.1.0b2 (gRPC) · SapBERT + BGE-M3 + CLIP ViT-B/32 · FastAPI + Pydantic v2 · React 18 + Vite + TanStack Query + Tailwind · pytest + Vitest.
>
> **Status.** Ingest runs clean against the real DB (60/60 cases). Demo query hits the engineered ground-truth record at confidence 0.79 (HIGH) with clause-level "Why This Matched" breakdowns. CLIP image upload finds the same case cross-modally. Backend has 223 tests, frontend 18. Everything in the repo is reproducible from `docker compose up -d && python ingest.py && uvicorn main:app`.

### Tech stack / technologies (as an array, DoraHacks usually wants comma-separated tags)

```
Actian VectorAI DB, Python, FastAPI, React, TypeScript, Vite, Tailwind CSS,
TanStack Query, Pydantic, pytest, Vitest, SapBERT, BGE-M3, CLIP,
HuggingFace Transformers, PyTorch, Docker, gRPC, Reciprocal Rank Fusion,
semantic search, vector database, AI/ML
```

### Tags to select (match what the hackathon page uses so we align on filterable facets)

- AI/ML
- python
- vector search
- vector databases
- databases

### Team

| Name | Role | GitHub |
|---|---|---|
| Stephen Sookra | Frontend, ingest, demo | @StephenSook |
| Vinh Le | Embeddings, search, API | @vinhbin |

### Repo URL

`https://github.com/StephenSook/trace-forensic-search`

### Demo video URL

*(TODO — Loom link. Task 5.2. Script lives at `DEMO_SCRIPT.md`.)*

### Live demo URL

N/A — local-first by design. Submission form may have an optional "Live URL" field; leave blank and reference the local-first constraint in the description.

### Thumbnail / cover image

*(TODO — if DoraHacks requires a cover image, take a screenshot of the results page with the "Why This Matched" panel expanded on UP-001. That's the single most legible image of what Trace does.)*

### License

MIT

---

## Pre-Submit Checklist

- [ ] Repo is public on github.com/StephenSook/trace-forensic-search
- [ ] README reflects current state (✅ done, commit `8cd8390`)
- [ ] Loom demo video uploaded and link copied (Task 5.2)
- [ ] All tests green on both sides (backend pytest · frontend vitest)
- [ ] `docker compose up` + `python ingest.py` + `uvicorn main:app` works cold on Stephen's machine — rehearse once
- [ ] Vinh's GitHub handle added to team table above
- [ ] Tags selected match the list above (AI/ML, python, vector search, vector databases, databases)
- [ ] Deadline timezone verified from logged-in DoraHacks view (the "12:00" banner vs. "18:00 UTC" timeline)
- [ ] Submit 2+ hours before the deadline — leave buffer for DoraHacks form upload issues

---

## Form Structure (from screenshots)

5-step wizard: **Profile → Details → Team → Contact → Submission**

Screenshots so far cover **Profile only**. Other 4 pages pending Stephen's next screenshots (form locks until Continue is pressed).

---

## Page 1 — Profile · Field-by-Field Mapping

| Form field | Required? | Use this value |
|---|---|---|
| BUIDL (project) name | ✅ | `Trace` |
| BUIDL logo | ✅ | `Trace Logo/trace-logo-square.png` (480×480 PNG) |
| Vision ("Describe the problem") | ✅ | See "Vision textbox" below |
| Category (one pill) | ✅ | **AI/Robotics** (closest fit; not "Other") |
| Is this BUIDL an AI Agent? | ✅ | **No** (Trace is retrieval, not agentic) |
| GitHub/Gitlab/Bitbucket | ✅ | `https://github.com/StephenSook/trace-forensic-search` |
| Project website (optional) | — | Leave blank (local-first, no hosted demo) |
| Demo video | ✅ | **YouTube link** — see "Demo Video Plan" below |
| Social links (1–3, min 1) | ✅ | Stephen's GitHub profile: `https://github.com/StephenSook` · optional: X/Twitter, LinkedIn |

### Vision textbox (paste target)

Character limit unknown — draft is tight so it fits even a 500-char cap. Adjust if DoraHacks shows a counter.

> 600,000 people are reported missing in the United States every year and 40,000 sets of unidentified human remains sit unmatched in the national system. Both live in NamUs, the federal database — but NamUs runs on keyword search. A family's "eagle tattoo on his right forearm" and a medical examiner's "avian motif dermagraphic, right ventral antebrachium" share zero characters. Under keyword search they never meet. Trace is the semantic bridge that connects them, running entirely on-device so restricted forensic PII never touches a cloud API.

---

## Demo Video Plan (revised after screenshot)

**Primary host: YouTube** (embeds inline on the DoraHacks BUIDL page — judges watch without leaving the submission). Loom stays as a secondary/backup link in the README.

Steps for Task 5.2:
1. Record the demo (script is `DEMO_SCRIPT.md`).
2. Export as 1080p MP4.
3. Upload to YouTube — **unlisted** is fine (embeds still work with unlisted). Don't make it private.
4. Title: `Trace — Semantic search for missing persons · Actian VectorAI DB Build Challenge`
5. Description: paste the short description from above + repo link + hackathon link.
6. Copy the YouTube URL into the Demo Video field.
7. Mirror to Loom and add the Loom link to the README for anyone who prefers that player.

---

## Logo Plan

Need a 480×480 mark. Two quick options in order of preference:

1. **Wordmark** — "trace" in a monospace font with a single pulsing dot or crosshair glyph alongside. Matches the terminal/forensic aesthetic of the UI. Takes 10 minutes in Figma or even a React-SVG render exported to PNG.
2. **Icon-only** — the `Wifi` / signal glyph currently in the FAB, white-on-dark, centered on the brand background. Fastest. Risk: generic.

If neither happens in time, a plain-text render of "TRACE" centered on the app's dark background color is an acceptable fallback. **Do not leave it blank** — the field is required and a missing logo is the first thing judges see.

---

## Still-Pending Questions (to answer from next screenshots)

- **Details page** — likely hosts the long writeup, tech stack, tags. Need to see character limits.
- **Team page** — Vinh's GitHub handle needs filling in; confirm whether DoraHacks requires each member to have a registered DoraHacks account.
- **Contact page** — email vs. Discord vs. Telegram fields; what's required.
- **Submission page** — any final confirmations, additional file uploads, license selection.
- Whether any field accepts markdown formatting.
