from __future__ import annotations

import json
import os
from typing import List, Optional
import urllib.request


class EmbeddingClient:
    def __init__(
        self,
        *,
        provider: str = "api",
        model: str = "text-embedding-3-small",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: int = 45,
    ):
        self.provider = (provider or "api").strip().lower()
        self.model = model
        self.api_base = api_base or os.getenv("EMBEDDING_API_BASE", "")
        self.api_key = api_key or os.getenv("EMBEDDING_API_KEY", "")
        self.timeout_seconds = int(timeout_seconds)

    def embed(self, text: str) -> List[float]:
        return self._embed_api(text)

    def _embed_api(self, text: str) -> List[float]:
        if not self.api_base or not self.api_key:
            return []

        # OpenAI-compatible embeddings
        payload = json.dumps({"model": self.model, "input": text}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.api_base.rstrip('/')}/embeddings",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        arr = data.get("data")
        if not isinstance(arr, list) or not arr:
            return []
        emb = arr[0].get("embedding")
        if not isinstance(emb, list):
            return []
        return [float(x) for x in emb]
