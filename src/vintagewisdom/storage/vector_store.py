from __future__ import annotations

from typing import Dict, List


class VectorStore:
    def __init__(self) -> None:
        self._vectors: Dict[str, List[float]] = {}

    def add(self, item_id: str, vector: List[float]) -> None:
        self._vectors[item_id] = vector

    def search(self, query_vector: List[float], top_k: int = 5) -> List[str]:
        if not self._vectors:
            return []
        # Placeholder: returns the first items until a real vector index is added.
        return list(self._vectors.keys())[:top_k]
