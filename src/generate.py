"""Grounded generation (Milestone 5).

ask(question) ties the whole pipeline together: retrieve top-k chunks, build a
context block that is the ONLY thing the LLM is allowed to use, call Groq's
llama-3.3-70b-versatile, and return the answer plus a programmatically-built
source list.

Grounding is enforced two ways:
  1. A strict system prompt: answer only from the numbered context; if it isn't
     there, say the exact refusal sentence.
  2. A relevance gate: chunks whose cosine distance exceeds MAX_DISTANCE are
     dropped, and if nothing relevant survives we refuse *without* calling the
     LLM — so an off-topic question can't be answered from training knowledge.

Source attribution is built from the retrieved chunks' metadata in Python, not
left to the model to invent.

Usage:
    python -m src.generate "is the meal plan required?"
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from src.retrieve import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TOP_K = 5
# Cosine distance above this = too loosely related to count as grounding.
MAX_DISTANCE = 0.75
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are an assistant that answers questions about student life at NJIT "
    "using ONLY the numbered context passages provided by the user. "
    "Follow these rules strictly:\n"
    "1. Use only facts stated in the context. Do not use any outside or prior "
    "knowledge.\n"
    f"2. If the context does not contain enough information to answer, reply "
    f"with exactly: \"{REFUSAL}\" and nothing else.\n"
    "3. Do not speculate, generalize, or add caveats from general knowledge.\n"
    "4. When you use a passage, cite it inline by its number like [1], [2]. "
    "Base your answer on what the passages actually say, including disagreement "
    "between student reviews when present."
)


def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set in environment/.env")
    return Groq(api_key=key)


def _format_context(hits: list[dict]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        src = h["metadata"]["source_name"]
        blocks.append(f"[{i}] (source: {src})\n{h['text']}")
    return "\n\n".join(blocks)


def ask(question: str, k: int = TOP_K) -> dict:
    """Return {'answer': str, 'sources': list[str], 'chunks': list[dict]}."""
    hits = retrieve(question, k=k)
    relevant = [h for h in hits if h["distance"] <= MAX_DISTANCE]

    # Relevance gate: nothing close enough -> refuse before calling the LLM.
    if not relevant:
        return {"answer": REFUSAL, "sources": [], "chunks": [], "retrieved": hits}

    context = _format_context(relevant)
    user_msg = (
        f"Context passages:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the passages above."
    )

    resp = _client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # Source list is built from metadata, not from the model's text.
    if answer.startswith(REFUSAL):
        sources = []
    else:
        seen, sources = set(), []
        for h in relevant:
            label = f"{h['metadata']['source_name']} ({h['metadata']['url']})"
            if label not in seen:
                seen.add(label)
                sources.append(label)
    return {"answer": answer, "sources": sources, "chunks": relevant,
            "retrieved": hits}


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python -m src.generate "your question"')
        sys.exit(1)
    result = ask(" ".join(sys.argv[1:]))
    print("\nANSWER:\n" + result["answer"])
    if result["sources"]:
        print("\nSOURCES:")
        for s in result["sources"]:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
