"""Embedding + vector store (Milestone 4).

Loads chunks.json (produced by src/ingest.py), embeds every chunk with
all-MiniLM-L6-v2, and stores the vectors + metadata in a persistent ChromaDB
collection. The collection uses cosine distance so scores land in ~[0, 1]:
0 = identical, lower = more relevant.

Usage:
    python -m src.embed          # (re)build the vector store from chunks.json
"""

from __future__ import annotations

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = ROOT / "chunks.json"
DB_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "njit_guide"
MODEL_NAME = "all-MiniLM-L6-v2"


def load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def get_collection(client: chromadb.ClientAPI, reset: bool = False):
    """Return the collection, optionally deleting any existing one first so a
    rebuild doesn't leave stale chunks behind."""
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet
    # cosine space -> distances in [0, 2], ~[0, 1] for relevant matches.
    return client.get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def build() -> None:
    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE.name}")

    model = load_model()
    texts = [c["text"] for c in chunks]
    print(f"Embedding with {MODEL_NAME} ...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = get_collection(client, reset=True)

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=[e.tolist() for e in embeddings],
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"Stored {collection.count()} chunks in ChromaDB at {DB_DIR.name}/")


if __name__ == "__main__":
    build()
