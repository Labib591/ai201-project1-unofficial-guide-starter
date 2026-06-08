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
| 1 | How does dining work and is the meal plan required? | Independent vendor, balanced meals; first-year & sophomores living on campus required to have a plan (A–E). | Correctly states dining runs on a meal-plan system via an independent vendor with Tech Bucks; first-year & sophomores required to pick plans A–E; upper-class plans optional. Cited the meal-plan and FAQ chunks. | Relevant (top 0.46) | **Accurate** |
| 2 | What do students say about internship and career outcomes? | 67% say alumni network is strong, 80% say career center was helpful, ~95% employed after graduation. | Mentioned NYC proximity for internships, co-op opportunities, one Merck placement, and a review about limited faculty career support — but **missed the headline outcome stats** (95% employed, 67%/80% polls). | Partially relevant | **Partially accurate** |
| 3 | How are the academic and recreational facilities at NJIT? | Modern labs/makerspaces, Wellness & Events Center, libraries; some maintenance/dining complaints. | Cited indoor pool, limited green space, freshman engineering class, Honors space, and food-quality complaints — captured the vibe but **missed the WEC, labs, and makerspaces** specifically. | Relevant (top 0.39) | **Partially accurate** |
| 4 | What is the cost to live on campus? | Per person/sem: double room ≈ $4,949–$5,313 (~$5,170 avg); apartments more. | Reported Niche's aggregate average housing ($9,950/yr) + meal-plan costs + 12-month contract surcharge. Grounded and correct, but **gave the aggregate average instead of the per-hall room rates** (which were retrieved at rank 4 but not used). | Relevant (top 0.34) | **Partially accurate** |
| 5 | How do I look for a job on campus? | Contact Student Financial Aid Services Office in the Student Mall; Residence Life also hires. | Exactly that — contact Student Financial Aid Services in the Student Mall; Residence Life hires students and posts positions. | Relevant (top 0.32) | **Accurate** |

**Summary:** 2/5 fully accurate, 3/5 partially accurate, 0/5 inaccurate. Every answer was grounded in retrieved context with no hallucinated facts; the partial cases are retrieval-recall problems (the right chunk existed but ranked outside top-k, or a more specific chunk was retrieved but the LLM preferred a higher-ranked aggregate), not generation problems.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "What do students say about internship and career outcomes?" (Evaluation Q2)

**What the system returned:** A grounded but incomplete answer — it cited NYC proximity for internships, co-op opportunities, one graduate's Merck placement, and a review complaining about limited faculty career support. It **omitted the headline outcome statistics** that best answer the question: 95% of graduates employed one year after graduation, 67% saying the alumni network is strong, and 80% saying the career center was helpful.

**Root cause (tied to a specific pipeline stage): retrieval recall, not generation.** Those statistics live in a single chunk in `06_niche_after_college_stats.txt`. When I print the ranked retrieval for this query, that chunk does not appear even in the **top 10** (the top-5 cutoff stops at cosine distance ~0.61). The cause is a **vocabulary mismatch between the query and the chunk at embedding time**: the question uses the words "internship" and "career outcomes," which `all-MiniLM-L6-v2` embeds close to the *Career Development Services* policy page (literally titled "Internships & Co-op") and to review prose that says "internship." The stats chunk instead phrases the same concept as "median earnings one year after graduation," "employed one year after graduation," and "loan default rate" — lexically distant from the query, so its embedding lands farther away. Because generation is hard-limited to the retrieved context, a chunk that never gets retrieved can never be cited, so the LLM answered correctly from weaker material and the strongest evidence was invisible to it.

**What you would change to fix it:** Three options, cheapest first. (1) **Raise top-k or add a per-`content_type` retrieval pass** — fetch the best few `ranking` chunks alongside the global top-k so quantitative stats always get a seat for outcome-style questions. (2) **Query expansion / HyDE** — embed a hypothetical answer ("95% of graduates are employed…") instead of the raw question, pulling the query embedding toward stat vocabulary. (3) **Enrich the stats chunk's text at ingestion** with a natural-language lead-in ("Career and employment outcomes for graduates:") so its embedding overlaps the query vocabulary. Option (1) is the smallest change and directly addresses the recall gap.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Deciding the per-source chunking strategy in `planning.md` *before* writing code turned chunking from an open-ended problem into a simple dispatch. Because the spec already said "RMP review = atomic, Niche = paragraph/stats-split, NJIT policy = heading-based," the implementation became a `manifest.json` that tags each file with a `strategy`, plus a `chunk_text(text, strategy)` function that just routes to the matching chunker. I never had to stop and re-decide granularity mid-build, and adding each newly-collected source was a one-line manifest entry rather than new code.

**One way your implementation diverged from the spec, and why:** The spec's metadata schema assumed Rate My Professors would give per-professor reviews tagged with `professor_name`, `department`, and `difficulty`. In practice RMP's per-professor pages are JavaScript-rendered and returned HTTP 403 / empty shells to every scraping attempt, so the only RMP content I could collect was **school-level** reviews with no professor attribution. The RMP chunks therefore carry `content_type: review` and a `rating`, but not the professor/department/difficulty fields the spec imagined — which is also why the demo question "Which professors get the best reviews for CS courses?" isn't well supported by the current corpus. A second, smaller divergence: the spec's fixed-size-with-overlap strategy for "job postings" is implemented but unused, because no standalone job-board source survived collection (Career Services became a `policy` source instead).

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Ingestion & chunking**

- *What I gave the AI:* My Chunking Strategy section from `planning.md` (the per-source rules and metadata schema) plus the Document Sources table, and asked it to implement the loading + cleaning + chunking pipeline.
- *What it produced:* `src/clean.py` (HTML/entity stripping, boilerplate removal), `src/chunk.py` with four strategies (atomic / paragraph / heading / fixed), and `src/ingest.py` driven by a `documents/manifest.json` that tags each file with its strategy and metadata.
- *What I changed or overrode:* Several Niche pages mixed survey stats with prose reviews. Rather than chunk each page with one strategy, I directed splitting every mixed page into two files — a reviews file (`atomic`, `content_type: review`) and a stats file (`paragraph`, `content_type: ranking`) — so factual and opinion content carry different metadata. I also had it de-duplicate reviews that appeared on multiple Niche pages, which the first version did not handle and which would otherwise have double-counted ~6 reviews.

**Instance 2 — Grounded generation**

- *What I gave the AI:* My grounding requirement (answer from retrieved context only, refuse when unsupported, cite sources) and the Retrieval Approach section.
- *What it produced:* `src/generate.py` with a strict system prompt and a Groq `llama-3.3-70b-versatile` call, returning an answer plus sources.
- *What I changed or overrode:* The first version relied entirely on the prompt to enforce grounding and asked the model to list its own sources. I overrode both: (1) added a **structural relevance gate** that drops chunks with cosine distance > 0.75 and returns the refusal sentence *without calling the LLM* when nothing relevant survives, so an off-topic question can't be answered from training knowledge; and (2) made the displayed source list **programmatic** — built in Python from the retrieved chunks' metadata — instead of trusting the model to cite, which guarantees attribution can't be hallucinated or dropped.
