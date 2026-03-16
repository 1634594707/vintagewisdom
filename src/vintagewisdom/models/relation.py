from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RelationEvidence(BaseModel):
    model_config = ConfigDict(extra="allow")

    case_id: str
    quote: str
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None


class Relation(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    source: str
    target: str
    relation_type: str
    confidence: float = 0.5
    attributes: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[RelationEvidence] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
