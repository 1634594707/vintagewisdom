from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class Pattern(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    domain: str
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    causal_chain: List[str] = Field(default_factory=list)
    intervention_points: List[str] = Field(default_factory=list)
    confidence_score: float | None = None
    case_count: int | None = None
    verified: bool = False
