"""Ingestion + chunking orchestrator (Milestone 3).

Reads documents/manifest.json, loads and cleans each source file, applies the
per-source chunking strategy, attaches metadata to every chunk, and writes the
result to chunks.json. Also prints an inspection report so you can eyeball
chunk quality before embedding.

Usage:
    python -m src.ingest                # ingest + write chunks.json + report
    python -m src.ingest --sample 5     # show N representative chunks (default 5)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src.clean import load_and_clean
from src.chunk import chunk_text

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "documents"
MANIFEST = DOCS_DIR / "manifest.json"
OUT_FILE = ROOT / "chunks.json"

_RATING_RE = re.compile(r"^Rating:\s*([0-9.]+)\s*/\s*5\s*\|\s*", re.I)


def _extract_rating(text: str) -> tuple[str, float | None]:
    """Pull a leading 'Rating: X/5 |' prefix out of a review chunk, if present."""
    m = _RATING_RE.match(text)
    if not m:
        return text, None
    return text[m.end():].strip(), float(m.group(1))


def build_chunks() -> list[dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    all_chunks: list[dict] = []

    for entry in manifest["sources"]:
        path = DOCS_DIR / entry["file"]
        if not path.exists():
            print(f"  ! missing file, skipping: {entry['file']}")
            continue

        text = load_and_clean(path)
        pieces = chunk_text(text, entry["strategy"])

        for i, piece in enumerate(pieces):
            meta = {
                "source": entry["source"],
                "source_name": entry["source_name"],
                "url": entry["url"],
                "content_type": entry["content_type"],
                "strategy": entry["strategy"],
            }
            if entry["content_type"] == "review":
                piece, rating = _extract_rating(piece)
                if rating is not None:
                    meta["rating"] = rating
            all_chunks.append({
                "id": f"{path.stem}::{i}",
                "text": piece,
                "metadata": meta,
            })

        print(f"  {entry['file']:<32} {entry['strategy']:<10} -> {len(pieces):>3} chunks")

    return all_chunks


def report(chunks: list[dict], sample: int) -> None:
    print("\n" + "=" * 70)
    print(f"TOTAL CHUNKS: {len(chunks)}")

    # Sanity checks for the classic chunking bugs.
    empties = [c for c in chunks if not c["text"].strip()]
    lengths = [len(c["text"]) for c in chunks]
    print(f"empty chunks: {len(empties)}   "
          f"min/avg/max chars: {min(lengths)}/{sum(lengths)//len(lengths)}/{max(lengths)}")
    if len(chunks) < 50:
        print("NOTE: under 50 chunks - add the blocked sources (Niche/Collegedunia) "
              "to documents/ to enrich the corpus.")
    elif len(chunks) > 2000:
        print("NOTE: over 2000 chunks - chunks may be too small.")

    # Show representative chunks spread evenly across the corpus.
    print("\n" + "-" * 70)
    print(f"{sample} REPRESENTATIVE CHUNKS:")
    step = max(1, len(chunks) // sample)
    for c in chunks[::step][:sample]:
        m = c["metadata"]
        tag = f"[{m['source']} | {m['content_type']} | {m['strategy']}]"
        rating = f" rating={m['rating']}" if "rating" in m else ""
        print(f"\n  {c['id']} {tag}{rating}")
        print(f"  ({len(c['text'])} chars) {c['text'][:300]}"
              + ("..." if len(c["text"]) > 300 else ""))
    print("=" * 70)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=5, help="chunks to print")
    args = ap.parse_args()

    print(f"Ingesting from {DOCS_DIR} ...")
    chunks = build_chunks()
    OUT_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(chunks)} chunks -> {OUT_FILE.relative_to(ROOT)}")
    report(chunks, args.sample)


if __name__ == "__main__":
    main()
