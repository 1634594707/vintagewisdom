from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class QdrantHit:
    id: str
    score: float
    payload: Dict[str, Any]


class QdrantVectorStore:
    def __init__(self, *, url: str, collection: str, vector_size: int | None = None):
        try:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.http import models as qm  # type: ignore
        except Exception as e:
            raise RuntimeError("Qdrant dependency not installed. Install with: pip install -e '.[graphrag]'") from e

        self._qm = qm
        self._client = QdrantClient(url=url)
        self._collection = collection
        self._vector_size = int(vector_size) if vector_size else None

    def ensure_collection(self, *, vector_size: int) -> None:
        vector_size = int(vector_size)
        try:
            cols = self._client.get_collections().collections
            if any(c.name == self._collection for c in cols):
                return
        except Exception:
            pass

        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=self._qm.VectorParams(size=vector_size, distance=self._qm.Distance.COSINE),
        )

    def upsert(self, *, points: List[Dict[str, Any]]) -> None:
        if not points:
            return
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, *, query_vector: List[float], top_k: int = 20, filter_case_ids: Optional[List[str]] = None) -> List[QdrantHit]:
        qf = None
        if filter_case_ids:
            qf = self._qm.Filter(
                must=[
                    self._qm.FieldCondition(
                        key="case_id",
                        match=self._qm.MatchAny(any=filter_case_ids),
                    )
                ]
            )

        res = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=int(top_k),
            with_payload=True,
            query_filter=qf,
        )
        out: List[QdrantHit] = []
        for p in res or []:
            out.append(QdrantHit(id=str(p.id), score=float(p.score or 0.0), payload=dict(p.payload or {})))
        return out
