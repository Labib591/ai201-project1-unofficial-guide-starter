"""Document loading and cleaning.

Turns a raw source file (.txt, .md, or .html) into clean plain text:
strips HTML tags and boilerplate, decodes HTML entities, and normalizes
whitespace. Heading markers ("# ...") are preserved so the heading-based
chunker can still see section boundaries.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from bs4 import BeautifulSoup

# Tags whose entire contents are boilerplate / non-content and should be dropped.
_STRIP_TAGS = ["script", "style", "nav", "header", "footer", "aside", "form",
               "noscript", "button", "svg"]

# Lines that are pure site boilerplate (cookie banners, share prompts, etc.).
_BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*(read more|share this|sign in|log in|subscribe)\b", re.I),
    re.compile(r"^\s*(cookie|we use cookies|accept all cookies)\b", re.I),
    re.compile(r"^\s*\d+\s*(comments?|shares?|likes?)\s*$", re.I),
]


def _clean_html(raw: str) -> str:
    """Extract readable text from an HTML document."""
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    # Convert headings to markdown-style markers so chunkers can detect them.
    for level in range(1, 7):
        for h in soup.find_all(f"h{level}"):
            h.insert_before("\n# ")
            h.insert_after("\n")
    return soup.get_text(separator="\n")


def _normalize(text: str) -> str:
    """Decode entities, drop boilerplate lines, and collapse whitespace."""
    text = html.unescape(text)              # &amp; -> &, &#39; -> '
    text = text.replace(" ", " ")      # non-breaking space
    text = re.sub(r"[ \t]+", " ", text)     # collapse runs of spaces/tabs

    kept = []
    for line in text.split("\n"):
        line = line.strip()
        if any(p.match(line) for p in _BOILERPLATE_PATTERNS):
            continue
        kept.append(line)

    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse blank-line runs
    return text.strip()


def load_and_clean(path: str | Path) -> str:
    """Load a source file and return cleaned plain text."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        raw = _clean_html(raw)
    return _normalize(raw)
