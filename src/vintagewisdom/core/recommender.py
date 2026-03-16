from __future__ import annotations

from typing import List

from ..models.case import Case


class Recommender:
    def recommend(self, query: str, cases: List[Case]) -> List[str]:
        if not cases:
            return ["Add at least one case and retry the query."]
        return ["Compare outcomes of similar cases.", "Identify key constraints and risks."]
