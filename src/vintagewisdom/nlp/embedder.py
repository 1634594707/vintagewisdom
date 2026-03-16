from __future__ import annotations

from typing import List


class Embedder:
    def embed(self, text: str) -> List[float]:
        # Placeholder embedding: length-based vector.
        return [float(len(text))]
