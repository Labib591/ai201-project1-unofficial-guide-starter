"""Retrieval (Milestone 4).

Embeds a query with the same model used at index time and returns the top-k
most similar chunks from ChromaDB, each with its source metadata and cosine
distance (lower = more relevant).

Usage:
    python -m src.retrieve "is the meal plan required?"     # ad-hoc query
    python -m src.retrieve --eval                            # run eval queries
"""

from __future__ import annotations

import argparse
import functools

import chromadb
from sentence_transformers import SentenceTransformer

from src.embed import DB_DIR, COLLECTION_NAME, MODEL_NAME

# The 5 evaluation-plan questions (planning.md > Evaluation Plan).
EVAL_QUERIES = [
    "How does dining work and is the meal plan required?",
    "What do students say about internship and career outcomes?",
    "How are the academic and recreational facilities at NJIT?",
    "What is the cost to live on campus?",
    "How do I look for a job on campus?",
]


@functools.lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@functools.lru_cache(maxsize=1)
def _collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_collection(COLLECTION_NAME)


def retrieve(query: str, k: int = 5, content_type: str | None = None) -> list[dict]:
    """Return the top-k chunks for a query.

    content_type: optionally restrict to 'review' | 'policy' | 'ranking' | 'job'
    so factual questions can prefer policy/ranking over opinion reviews.
    """
    embedding = _model().encode([query], normalize_embeddings=True)[0].tolist()
    where = {"content_type": content_type} if content_type else None
    res = _collection().query(query_embeddings=[embedding], n_results=k, where=where)

    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append({"text": doc, "metadata": meta, "distance": dist})
    return hits


def _print_hits(query: str, hits: list[dict]) -> None:
    print(f"\nQUERY: {query}")
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        flag = "" if h["distance"] < 0.5 else "  <-- weak (>0.5)"
        print(f"  [{i}] dist={h['distance']:.3f}  "
              f"{m['source']}/{m['content_type']}{flag}")
        print(f"      {h['text'][:200]}" + ("..." if len(h["text"]) > 200 else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="query string")
    ap.add_argument("--eval", action="store_true", help="run all eval queries")
    ap.add_argument("-k", type=int, default=5)
    args = ap.parse_args()

    if args.eval:
        for q in EVAL_QUERIES:
            _print_hits(q, retrieve(q, k=args.k))
    elif args.query:
        _print_hits(args.query, retrieve(args.query, k=args.k))
    else:
        ap.error("provide a query or --eval")


if __name__ == "__main__":
    main()
