# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

This system covers the full unofficial student experience at NJIT — the practical, on-the-ground knowledge that incoming freshmen need to actually navigate college life. 

Incoming freshmen don't need another brochure — they need honest answers to questions like "Is Cypress Hall worth it or should I try to get into Martinson?" or "Is Professor X actually as tough as people say?"

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors — NJIT School Page | Student reviews (professor ratings) | https://www.ratemyprofessors.com/school/668 |
| 2 | Niche — NJIT General Reviews | Student reviews (overall experience) | https://www.niche.com/colleges/new-jersey-institute-of-technology/reviews/ |
| 3 | Niche — NJIT Academics Page | Student reviews (courses & faculty) | https://www.niche.com/colleges/new-jersey-institute-of-technology/academics/ |
| 4 | Niche — NJIT Campus Life Page | Student reviews + survey data (dorms, food, safety, social) | https://www.niche.com/colleges/new-jersey-institute-of-technology/campus-life/ |
| 5 | Niche — NJIT Graduate Reviews | Student reviews (grad student perspective) | https://www.niche.com/graduate-schools/new-jersey-institute-of-technology/reviews/ |
| 6 | NJIT Official Residence Halls Page | Official documentation (dorm options & amenities) | https://www.njit.edu/life/residence-halls |
| 7 | NJIT Residence Life FAQ | Official documentation (housing policy & procedures) | https://www.njit.edu/reslife/faq.php |
| 8 | NJIT Career Development Services | Official documentation (internships, Handshake, career fairs) | https://www.njit.edu/careerservices/ |
| 9 | Patch — "Inside Colleges: NJIT" | Journalistic/community perspective (campus overview, safety, Newark context) | https://patch.com/new-jersey/bridgewater/bp--inside-colleges-new-jersey-institute-of-technology |
| 10 | NJIT Meal Plan | Official Documentation | https://www.njit.edu/reslife/meal-plan-rates |
| 11 | NJIT Room Cost | Official Documentation | https://www.njit.edu/reslife/rates.php |
---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** Per-source, not one fixed size (see planning.md > Chunking Strategy). Reviews = one review per chunk (atomic); NJIT policy pages = one section per `#` heading; Patch prose = paragraph chunks merged to a ~200-char minimum; job postings (when added) = fixed 512-token window. Observed chunk sizes: 95–513 chars, ~277 avg.

**Overlap:** ~50 tokens on the fixed-size strategy only. The atomic, heading, and paragraph strategies split on natural boundaries (a whole review, a whole section) so no overlap is needed.

**Preprocessing before chunking:** Each source file runs through `src/clean.py` — strips HTML + boilerplate tags (nav/footer/script), decodes HTML entities (`&amp;`, `&#39;`, non-breaking spaces), drops cookie/share/"read more" boilerplate lines, and normalizes whitespace. HTML `<h1>`–`<h6>` are converted to `#` markers so the heading chunker still sees section boundaries.

**Why these choices fit your documents:** The corpus mixes short opinion reviews with hierarchical policy pages, so one global chunk size would either shred the policy sections or merge unrelated reviews. Matching the strategy to each source's structure keeps every chunk a single retrievable thought.

**Final chunk count:** 98 across 13 source files. Seven sources were scraped directly (NJIT pages, Patch, RMP school page); the Niche pages returned HTTP 403, and the NJIT meal-plan and room-rate tables were pasted in manually, then all were cleaned. Each mixed Niche page was split into a reviews file (atomic) and a stats file (ranking), matching the stats-vs-prose chunking rule; the rate tables were chunked by heading so each hall's full rate list stays in one chunk. Duplicate reviews appearing on multiple Niche pages were de-duplicated during cleaning.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, runs locally, no API key). Chunks are embedded with `normalize_embeddings=True` and stored in a persistent ChromaDB collection configured for **cosine** distance (`hnsw:space: cosine`), so retrieval scores land in ~[0, 1] where lower = more relevant. Each chunk is stored with its full metadata (source, source_name, url, content_type, strategy, and rating where applicable), enabling `content_type`-filtered retrieval. Default top-k = 5. Verified retrieval: all 5 evaluation queries return a top-1 chunk from the correct source with cosine distance between 0.32 and 0.46.

**Production tradeoff reflection:** MiniLM wins here on speed and zero cost. If cost weren't a constraint I'd weigh a larger model (e.g. `text-embedding-3-large` or a BGE/E5 model) on four axes: **domain accuracy** (bigger models capture nuance in slangy reviews that MiniLM flattens), **context length** (policy chunks can exceed MiniLM's ~256-token window and get truncated), **multilingual support** (some international-student reviews would benefit from a multilingual model), and **latency** (an API model adds round-trips MiniLM avoids locally). For a real deployment I'd move to a larger-context, domain-tuned model and accept the added cost/latency for better retrieval on policy pages and multilingual reviews.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The LLM (`llama-3.3-70b-versatile` via Groq, temperature 0) is given a system prompt that allows it to use **only** the numbered context passages: "Use only facts stated in the context. Do not use any outside or prior knowledge. If the context does not contain enough information to answer, reply with exactly: 'I don't have enough information on that.' ... Do not speculate, generalize, or add caveats from general knowledge." The retrieved chunks are passed as a numbered context block, and the user turn ends with "Answer using only the passages above."

**Structural grounding (beyond the prompt):** A relevance gate in `src/generate.py` drops any retrieved chunk whose cosine distance exceeds 0.75; if no chunk survives, the system returns the refusal sentence **without calling the LLM at all**, so an off-topic question physically cannot be answered from training knowledge. This was verified — e.g. "What is the wifi password for the dorms?" returns "I don't have enough information on that." with no sources.

**How source attribution is surfaced in the response:** Two layers. (1) The model cites passages inline by number (`[1]`, `[2]`). (2) The displayed **source list is built programmatically in Python** from the retrieved chunks' metadata (`source_name` + `url`) — it is not generated by the LLM, so attribution can't be hallucinated or omitted. On a refusal the source list is empty. The Gradio UI (`app.py`) shows the answer and the "Retrieved from" source list in separate fields.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
