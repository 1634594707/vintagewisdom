from __future__ import annotations

from typing import Dict


class PatternStore:
    def __init__(self) -> None:
        self._patterns: Dict[str, dict] = {}

    def add(self, pattern_id: str, data: dict) -> None:
        self._patterns[pattern_id] = data

    def get(self, pattern_id: str) -> dict | None:
        return self._patterns.get(pattern_id)
