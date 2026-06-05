# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

This system covers the full unofficial student experience at NJIT — the practical, on-the-ground knowledge that incoming freshmen need to actually navigate college life. 

Incoming freshmen don't need another brochure — they need honest answers to questions like "Is Cypress Hall worth it or should I try to get into Martinson?" or "Is Professor X actually as tough as people say?"

Demo Questions-
     1. Is on-campus housing at NJIT worth it for freshmen?
     2. Which professors get the best reviews for CS courses?
     3. How does dining work and is the meal plan required?
     4. What's it like living in Harrison vs. on campus?
     5. What do students say about internship and career outcomes?
---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors — NJIT School Page | Student reviews (professor ratings) | https://www.ratemyprofessors.com/school/668 |
| 2 | Niche — NJIT General Reviews | Student reviews (overall experience) | https://www.niche.com/colleges/new-jersey-institute-of-technology/reviews/ |
| 3 | Niche — NJIT Academics Page | Student reviews (courses & faculty) | https://www.niche.com/colleges/new-jersey-institute-of-technology/academics/ |
| 4 | Niche — NJIT Campus Life Page | Student reviews + survey data (dorms, food, safety, social) | https://www.niche.com/colleges/new-jersey-institute-of-technology/campus-life/ |
| 5 | Niche — NJIT Graduate Reviews | Student reviews (grad student perspective) | https://www.niche.com/graduate-schools/new-jersey-institute-of-technology/reviews/ |
| 6 | Collegedunia — NJIT Student Reviews | Student reviews (international & grad perspective) | https://s3.collegedunia.com/usa/university/1750-new-jersey-institute-of-technology-newark/reviews |
| 7 | NJIT Official Residence Halls Page | Official documentation (dorm options & amenities) | https://www.njit.edu/life/residence-halls |
| 8 | NJIT Residence Life FAQ | Official documentation (housing policy & procedures) | https://www.njit.edu/reslife/faq.php |
| 9 | NJIT Career Development Services | Official documentation (internships, Handshake, career fairs) | https://www.njit.edu/careerservices/ |
| 10 | Patch — "Inside Colleges: NJIT" | Journalistic/community perspective (campus overview, safety, Newark context) | https://patch.com/new-jersey/bridgewater/bp--inside-colleges-new-jersey-institute-of-technology |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
