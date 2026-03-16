from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class TextChunk:
    chunk_id: str
    text: str


def chunk_text(*, text: str, max_chars: int = 1400, overlap_chars: int = 200) -> List[TextChunk]:
    s = (text or "").strip()
    if not s:
        return []

    max_chars = max(200, int(max_chars or 1400))
    overlap_chars = max(0, min(int(overlap_chars or 0), max_chars - 50))

    out: List[TextChunk] = []
    start = 0
    idx = 0
    n = len(s)
    while start < n:
        end = min(n, start + max_chars)
        piece = s[start:end].strip()
        if piece:
            out.append(TextChunk(chunk_id=f"c{idx}", text=piece))
            idx += 1
        if end >= n:
            break
        start = max(0, end - overlap_chars)

    return out
