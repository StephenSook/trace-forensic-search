# Trace — Demo Script

**Target length:** 3:30–4:00 · **Format-flexible:** works as a live pitch or a pre-recorded Loom voiceover
**Speakers:** Stephen (S) · Vinh (V) · or solo if format requires one presenter
**Demo day:** April 18, 2026

---

## 0:00–0:35 · The Problem (Stephen)

> **S:** 600,000 people are reported missing in the United States every year. 40,000 sets of unidentified human remains sit in the national system. The data to match them already exists — it lives in a federal database called NamUs. But NamUs runs on keyword search.
>
> A mother looking for her son describes an **eagle tattoo on his right forearm**. The medical examiner's record reads **"avian motif dermagraphic, right ventral antebrachium."** Same person. Zero shared vocabulary. Keyword search never makes the connection.
>
> Not because the match doesn't exist. Because there is no semantic bridge between how families talk and how forensics writes.

**Beat.**

> **S:** Trace is that bridge.

*(On-screen: landing page, logo, "Trace — semantic search for missing persons")*

---

## 0:35–0:50 · The Impossible Query (Stephen)

> **S:** I'm going to type, in plain English, what a family might actually say.

*(Type slowly into the search box — let the judges read along):*

```
My brother went missing in 2019 in Tennessee. He was 34,
about 6 feet tall, had a distinctive tattoo of an eagle on
his right forearm, and was last seen near a highway.
```

> **S:** None of those words appear in any forensic record. But watch what happens when we tell Trace to search *only* unidentified remains in Tennessee — the cases where a medical examiner wrote the record, not a family.

*(Set CASE TYPE to "Unidentified Remains" and STATE to "Tennessee".)*

**Hit EXECUTE SEMANTIC QUERY.**

---

## 0:50–1:40 · The Demo Moment (Stephen)

*(Results load — one result: UP-001, confidence 0.55 MEDIUM)*

> **S:** One match. Case UP-001. Unidentified male found in 2020, Tennessee. Medium confidence — 0.55.

> **S:** This is an unidentified remains case. The family never wrote this record — a medical examiner did, using clinical forensic vocabulary. The confidence is medium, not high, and that's exactly why this problem is hard. The two vocabularies share zero words. But Trace still found the connection.

*(Click "WHY THIS MATCHED" — the translation table expands)*

> **S:** This panel is the whole point of Trace. Every row shows the family's words on the left, and the forensic phrasing that matched on the right.

*(Walk through the rows, slowly):*

> - **"was last seen near a highway"** matched **RECOVERY_LOCATION** — *"Recovered along I-40 corridor east of Nashville, 2020."* The family said "near a highway." The examiner said "I-40 corridor." Same location, different vocabulary. Similarity 0.62.
> - **"about 6 feet tall"** matched **CLOTHING_EFFECTS** — *"Denim trousers, dark forest-toned plaid overshirt, heavy-soled leather footwear."* Similarity 0.53.
> - **"had a distinctive tattoo of an eagle on his right forearm"** matched **DISTINGUISHING_MARKS** — *"avian motif dermagraphic on right ventral antebrachium."* The family said "eagle tattoo on his right forearm." The medical examiner wrote "avian motif dermagraphic, right ventral antebrachium." Zero shared words. Trace bridged the gap. Similarity 0.51.
> - **"My brother went missing in 2019 in Tennessee"** matched **RECOVERY_LOCATION** — the system connected the state and timeframe to the forensic recovery record. Similarity 0.44.

*(Click "VIEW FULL CASE FILE")*

> **S:** Full case file. Physical description: *"avian motif dermagraphic on right ventral antebrachium"* — that's "eagle tattoo on his right forearm" in medical-examiner speak. Recovery: *"along I-40 corridor east of Nashville."* Every field is written in forensic vocabulary. A keyword search for "eagle tattoo" would never find this record. Trace did.

*(Brief pause on the case detail page.)*

---

## 1:40–2:40 · How It Works (Vinh)

> **V:** The reason this works is Actian VectorAI DB. And we use it as a first-class primitive, not a generic vector store.

*(Optional: show the architecture diagram or the named-vector table from the README)*

> **V:** Every case is stored across **four independent named vector spaces** on a single collection.
>
> - **Physical description** goes through SapBERT — a biomedical language model — because the lay-to-forensic terminology gap is most acute there.
> - **Circumstances** and **clothing** go through BGE-M3.
> - **Tattoo and identifying photos** go through CLIP, for cross-modal image search.
>
> We deliberately did not embed the whole case as one vector. That dilutes the signal.

**Pause.**

> **V:** When a query comes in, it runs through four stages.

*(Count on fingers or tick through on-screen):*

> 1. **Hard filter first** — state, sex, age range, date window — using Actian's native filter DSL. We never spend recall budget on wrong-state or wrong-sex candidates.
> 2. **Multi-vector retrieval** — each named space searched independently.
> 3. **Hybrid fusion** — Reciprocal Rank Fusion with k equals sixty. Beats weighted-sum every time with no tuning.
> 4. **Ranked output** — with the per-dimension score breakdown and the terminology panel you just saw.

---

## 2:40–3:15 · Why Local-First (Stephen)

> **S:** One more thing. Trace runs entirely on-device.

*(Optional: `docker ps` shows the one Actian container. No network tab activity.)*

> **S:** Forensic data contains restricted PII — DNA profiles, dental records, unredacted case details. Sending that to a cloud API is a regulatory non-starter for the people we built this for. So Trace has zero external calls after setup. Actian runs in one local Docker container. The embedding models run natively. The whole stack fits on a laptop.
>
> That's not a feature. That's a requirement for this problem domain.

---

## 3:15–3:45 · Close (Stephen + Vinh)

> **S:** We built Trace for the Actian VectorAI DB Build Challenge. It bridges the vocabulary gap between a family's grief and a medical examiner's record — and it does it without ever touching the cloud.

> **V:** The data to connect 600,000 missing people to 40,000 unidentified remains already exists. What was missing was a semantic bridge.

> **S:** We're Stephen and Vinh. This is Trace. Thank you.

---

## Backup Narrative (if the demo breaks)

Do **not** troubleshoot on camera. Pivot cleanly:

> "The live environment isn't cooperating right now — let me walk you through the same result from our recorded trace."

Then show either:
- A screenshot of the UP-001 result card (Case Type set to "Unidentified Remains") with the "WHY THIS MATCHED" panel expanded, OR
- A screen recording clip of the same query running against the real backend.

Have both pre-loaded in a second browser tab before you start.

---

## Format Contingencies

**If the format is live + Q&A:**
- Rehearse the query once cold before going on — cold boot of the embedding models is ~3 seconds.
- Have a second laptop on the stage Wi-Fi as a fallback.
- Q&A: expect "why these four models?", "why RRF over learned re-rankers?", "how does this scale past 60 cases?" — answers in the appendix below.

**If the format is pre-recorded (Loom):**
- Record in 1080p, system audio muted except for your voice.
- Do two takes — one at normal pace, one 10% slower. The judges can always speed up; they can't slow you down.
- Export as MP4, upload to YouTube (unlisted). Paste YouTube URL into DoraHacks Demo Video field. Mirror to Loom as backup link in README.

**If it's Stephen solo** (Vinh unavailable or can't join):
- Stephen delivers both voices. Compress the "How It Works" section to 45 seconds.
- Skip the finger-counting — just speak the four stages in one breath.

---

## Scoring-Rubric Callouts (internal only — don't say these out loud)

Each of these has at least one moment in the script:

| Rubric dimension | Where it lands |
|---|---|
| **Use of Actian VectorAI DB (30%)** | "four named vector spaces", "native filter DSL", "points.search with `using`" |
| **Innovation** | "zero shared vocabulary", SapBERT for lay-to-forensic gap, RRF fusion, case_type filter isolates the semantic bridge |
| **Technical execution** | four-stage pipeline, MEDIUM confidence result on UP-001 (cross-vocabulary is hard), sub-second latency |
| **Impact** | 600K / 40K stat, "avian motif dermagraphic" ↔ "eagle tattoo" live on screen, local-first ethics |
| **Presentation quality** | translation panel showing forensic↔family vocabulary, clean case detail, rehearsed timing |

---

## Q&A Appendix

**"Why those four models specifically?"**
SapBERT for the physical description because it's trained on biomedical literature — it's the only model that knows "avian motif dermagraphic" and "eagle tattoo" are the same concept. BGE-M3 for circumstances and clothing because it's a strong general-purpose retrieval model with dense + sparse output on a single pass. CLIP because it's the cross-modal workhorse for the image space. All three are open-weight and run locally.

**"Why RRF over learned re-rankers?"**
Two reasons. One: RRF has no hyperparameters to tune — k=60 is the published default and it works. A learned re-ranker would require labeled training data we don't have for the forensic domain. Two: RRF is interpretable. We can show the judges and, more importantly, a medical examiner, exactly why a case ranked where it did.

**"How does this scale past 60 synthetic cases?"**
The architecture is unchanged. Actian VectorAI DB handles the index; the hard pre-filter keeps recall cost bounded even at NamUs scale. The synthetic dataset is 60 cases because we engineered a known ground-truth pair for the demo — the real deployment would ingest the full NamUs export.

**"Why synthetic data?"**
Two reasons. Ethics: we won't ingest real unsolved cases into a demo app — that would imply the app is operating on those cases. Reproducibility: synthetic data gives us a known ground-truth pair so we can demonstrate the "Why This Matched" panel with a pre-verified answer.

**"Can a family actually use this?"**
Not today — today this is a proof of the semantic bridge. A family-facing product would need moderation, advocate review, and NamUs integration. What we've built is the core retrieval technology. The user in front of this should be an investigator, a medical examiner's office, or a trained advocate.
