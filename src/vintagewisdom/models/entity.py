from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
