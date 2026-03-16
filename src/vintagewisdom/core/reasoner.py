from __future__ import annotations

from typing import List

from ..models.case import Case


class Reasoner:
    def analyze(self, query: str, cases: List[Case]) -> str:
        if not cases:
            return "No matching cases found yet. Add cases to improve recall."
        return f"Found {len(cases)} similar case(s). Review outcomes before deciding."
