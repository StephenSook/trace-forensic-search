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

*(Results load — one result: UP-001, confidence 0.79 HIGH)*

> **S:** One match. Case UP-001. Unidentified male found in 2020, Tennessee. High confidence — 0.79.

> **S:** This is an unidentified remains case. The family never wrote this record — a medical examiner did, using clinical forensic vocabulary. The two vocabularies share zero words. But Trace bridged the gap — high confidence, cross-vocabulary.

*(Click "WHY THIS MATCHED" — the translation table expands)*

> **S:** This panel is the whole point of Trace. Every row shows the family's words on the left, and the forensic phrasing that matched on the right.

*(Walk through the rows, slowly):*

> - **"was last seen near a highway"** matched **RECOVERY_LOCATION** — *"Found in a partially wooded area beside the highway."* The family said "near a highway." The examiner said "beside the highway." Same location, different framing. Similarity 0.79.
> - **"had a distinctive tattoo of an eagle on his right forearm"** matched **DISTINGUISHING_MARKS** — *"avian motif dermagraphic depicting raptor on right ventral antebrachium."* The family said "eagle tattoo on his right forearm." The medical examiner wrote "avian motif dermagraphic depicting raptor, right ventral antebrachium." Zero shared vocabulary. Trace bridged the gap. Similarity 0.65.
> - **"My brother went missing in 2019 in Tennessee"** matched **DISCOVERY_DATE** — the system connected the state and timeframe to the forensic recovery record. Similarity 0.57.
> - **"He was 34"** matched **PHYSICAL_DESCRIPTION** — *"mid-30s."* The family gave a specific age. The examiner estimated a range. Trace understood they're the same. Similarity 0.49.

*(Click "VIEW FULL CASE FILE")*

> **S:** Full case file. Physical description: *"avian motif dermagraphic depicting raptor on right ventral antebrachium"* — that's "eagle tattoo on his right forearm" in medical-examiner speak. Recovery: *"near highway I-40 east of Nashville."* Every field is written in forensic vocabulary. A keyword search for "eagle tattoo" would never find this record. Trace did.

*(Brief pause on the case detail page. Then navigate back to results.)*

---

## 1:40–2:10 · "One More Thing" — Image Upload (Stephen)

> **S:** One more thing. Trace doesn't just search with text. What if the family has a photo?

*(Click the CLIP IMAGE SEARCH upload button. Select `eagle.png` from Desktop. Leave the query text empty or as-is. Hit EXECUTE SEMANTIC QUERY.)*

> **S:** This is a photo of an eagle tattoo — the kind of reference photo a family might bring to an investigator. Trace encodes it with CLIP and searches across the image vector space.

*(Results load — UP-001 appears, confidence ~0.51 MEDIUM)*

> **S:** Same case. UP-001. The confidence is lower — 0.51, medium — because cross-modal matching is inherently harder. We're comparing a photograph to a text description that was never meant to be matched to an image. But it still found the right case. Text bridged the vocabulary gap. Now images bridge the modality gap.

*(Brief pause, then move on.)*

---

## 2:10–3:00 · How It Works (Vinh)

> **V:** The reason this works is Actian VectorAI DB. And we use it as a first-class primitive, not a generic vector store.

*(ELI10: it's our special notebook that understands meaning, not just words)*

*(Show one of these while talking — pick whichever feels right in the moment):*
- **3D Knowledge Graph** (recommended): open `trace-knowledge-graph.html` locally in browser — let it auto-rotate, have it as a background tab you can switch to if judges ask architecture questions
- **Mermaid diagram**: Vinh's backend architecture flowchart — static but clear, good if screen-sharing is unreliable
- **Architecture diagram or named-vector table**: from the README, good fallback if screen-sharing is unreliable

> **V:** Every case is stored across **four independent named vector spaces** on a single collection.
>
> - **Physical description** → **SapBERT** by Cambridge, trained on PubMed — so when a family says "eagle tattoo on his forearm," it matches a record that says "avian tattoo, right antebrachium." Same meaning, completely different words.
> - **Circumstances** → **BGE-M3** by BAAI — handles long narrative text and multiple languages, because not every family writes in English or writes the same way.
> - **Clothing** → **BGE-M3** by BAAI — same model, kept separate so a strong clothing match doesn't get averaged away by a weak location match.
> - **Identifying photos** → **CLIP** by OpenAI — the only model that puts images and text in the same space, so a description can match against an actual photo.
>
> We deliberately did not embed the whole case as one vector. That dilutes the signal.

*(ELI10: instead of describing a person in one paragraph, we put "what they looked like", "where they disappeared", "what they wore", and "their photo" into four separate folders — so "eagle tattoo on right forearm" scores strongly in the physical folder without being dragged down by a weak clothing or location match)*

**Pause.**

> **V:** When a query comes in, it runs through four stages.

*(Count on fingers or tick through on-screen):*

> 1. **Hard filter first** — state, age range, date window — using Actian's native filter DSL. We never spend recall budget on wrong-state or out-of-range candidates.
> *(ELI10: if a family says "he was in his 30s," we immediately throw out every case where the medical examiner estimated age 60+ — no point searching those)*
> 2. **Multi-vector retrieval** — each named space searched independently.
> *(ELI10: we search all four folders separately — the tattoo folder, the clothing folder, the circumstances folder, the photo folder — and collect the best matches from each)*
> 3. **Hybrid fusion** — Reciprocal Rank Fusion with k equals sixty. Beats weighted-sum every time with no tuning.
> *(ELI10: whoever kept appearing near the top across multiple folders wins — a case that matches on both the tattoo and the last location ranks higher than one that only matches on clothing)*
> 4. **Ranked output** — with the per-dimension score breakdown and the terminology panel you just saw.
> *(ELI10: we show the detective exactly which clue matched — "eagle tattoo" linked to this case's distinguishing marks, with a 91% similarity score)*

---

## 3:00–3:30 · Why Local-First (Stephen)

> **S:** One more thing. Trace runs entirely on-device.

*(Optional: `docker ps` shows the one Actian container. No network tab activity.)*

> **S:** Forensic data contains restricted PII — DNA profiles, dental records, unredacted case details. Sending that to a cloud API is a regulatory non-starter for the people we built this for. So Trace has zero external calls after setup. Actian runs in one local Docker container. The embedding models run natively. The whole stack fits on a laptop.
>
> That's not a feature. That's a requirement for this problem domain.

---

## 3:30–4:00 · Close (Stephen + Vinh)

> **S:** We built Trace for the Actian VectorAI DB Build Challenge. It bridges the vocabulary gap between a family's grief and a medical examiner's record — and it does it without ever touching the cloud.

> **V:** The data to connect 600,000 missing people to 40,000 unidentified remains already exists. What was missing was a semantic bridge.

*(Play the Gource time-lapse — 5 seconds of the repo growing from first commit to final state. Let it run while delivering the closing line.)*

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
| **Use of Actian VectorAI DB (30%)** | "four named vector spaces", "native filter DSL", "points.search with `using`", CLIP image vector space for cross-modal search |
| **Innovation** | "zero shared vocabulary", SapBERT for lay-to-forensic gap, RRF fusion, case_type filter isolates the semantic bridge, cross-modal image→text matching |
| **Technical execution** | four-stage pipeline, HIGH confidence 0.79 on UP-001 (cross-vocabulary, zero shared words), CLIP image upload finds same case at 0.51, sub-second latency |
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

**"Why named vectors instead of one collection?"**
A missing person has four completely different types of information — physical description, circumstances, clothing, and photos. Each needs a different model to understand it. If we embedded everything into one vector, a strong clothing match would average out against a weak location match and dilute the signal. Named vectors let us search all four simultaneously in one query and score each dimension independently.

**"Why run locally instead of using a cloud API?"**
Forensic data contains restricted PII — DNA profiles, dental records, unredacted case details. Sending that to a cloud API is a regulatory non-starter for the agencies we built this for. Local-first isn't a tradeoff, it's a requirement for this domain.

**"Can a family actually use this?"**
Not today — today this is a proof of the semantic bridge. A family-facing product would need moderation, advocate review, and NamUs integration. What we've built is the core retrieval technology. The user in front of this should be an investigator, a medical examiner's office, or a trained advocate.
