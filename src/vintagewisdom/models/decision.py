from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class DecisionLog(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    query: str
    context: Dict[str, Any] = Field(default_factory=dict)
    recommended_cases: List[str] = Field(default_factory=list)
    user_decision: str | None = None
    predicted_outcome: str | None = None
    actual_outcome: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evaluated_at: datetime | None = None
