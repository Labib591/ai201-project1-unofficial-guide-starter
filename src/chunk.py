"""Per-source chunking strategies (see planning.md > Chunking Strategy).

Each strategy takes cleaned text and returns a list of chunk strings. The
ingest orchestrator picks the strategy per source from documents/manifest.json
and attaches metadata afterward.

  atomic     -> one record (review) per chunk; split on blank lines
  paragraph  -> one paragraph per chunk; split on blank lines (+ merge tiny ones)
  heading    -> one "# Heading" section per chunk
  fixed      -> fixed-size window with overlap (for dense/semi-structured text)
"""

from __future__ import annotations

import re

# Drop anything shorter than this after splitting — guards against fragments
# and empty strings (a common chunking bug).
MIN_CHUNK_CHARS = 25


def _blank_line_blocks(text: str) -> list[str]:
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def chunk_atomic(text: str) -> list[str]:
    """One review = one chunk. Reviews are separated by blank lines."""
    return _blank_line_blocks(text)


def chunk_paragraph(text: str, min_chars: int = 200) -> list[str]:
    """One paragraph per chunk, merging very short paragraphs into the next
    so single-sentence fragments don't become standalone chunks."""
    blocks = _blank_line_blocks(text)
    merged: list[str] = []
    buffer = ""
    for block in blocks:
        buffer = f"{buffer}\n\n{block}".strip() if buffer else block
        if len(buffer) >= min_chars:
            merged.append(buffer)
            buffer = ""
    if buffer:
        if merged:
            merged[-1] = f"{merged[-1]}\n\n{buffer}"
        else:
            merged.append(buffer)
    return merged


def chunk_heading(text: str) -> list[str]:
    """One '# Heading' section per chunk. The heading line is kept inside the
    chunk so it carries context (e.g. 'Meal Plans & Food Services')."""
    sections: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        if re.match(r"^#{1,6}\s+\S", line):
            if current:
                sections.append("\n".join(current).strip())
            current = [line.lstrip("# ").strip()]  # heading as plain title line
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    # If the doc had no headings at all, fall back to paragraph chunking.
    if len(sections) <= 1 and not any(re.match(r"^#", l) for l in text.split("\n")):
        return chunk_paragraph(text)
    return [s for s in sections if s]


def chunk_fixed(text: str, size_tokens: int = 512, overlap_tokens: int = 50) -> list[str]:
    """Fixed-size sliding window with overlap. Tokens are approximated by
    whitespace-separated words, which is close enough for chunk sizing."""
    words = text.split()
    if not words:
        return []
    step = max(1, size_tokens - overlap_tokens)
    chunks = []
    for start in range(0, len(words), step):
        window = words[start:start + size_tokens]
        chunks.append(" ".join(window))
        if start + size_tokens >= len(words):
            break
    return chunks


_STRATEGIES = {
    "atomic": chunk_atomic,
    "paragraph": chunk_paragraph,
    "heading": chunk_heading,
    "fixed": chunk_fixed,
}


def chunk_text(text: str, strategy: str) -> list[str]:
    """Dispatch to the named strategy and filter out empty/fragment chunks."""
    if strategy not in _STRATEGIES:
        raise ValueError(f"Unknown strategy '{strategy}'. "
                         f"Choose from {sorted(_STRATEGIES)}.")
    chunks = _STRATEGIES[strategy](text)
    return [c.strip() for c in chunks if len(c.strip()) >= MIN_CHUNK_CHARS]
