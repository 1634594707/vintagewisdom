from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from ..utils.helpers import utc_now


class Case(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    domain: str
    title: str
    description: str | None = None
    decision_node: str | None = None
    action_taken: str | None = None
    outcome_result: str | None = None
    outcome_timeline: str | None = None
    lesson_core: str | None = None
    confidence: str | None = None
    domain_tags: str | None = None
    tags: list[str] | None = None  # 新增标签字段
    created_at: datetime | None = Field(default_factory=utc_now)
    updated_at: datetime | None = Field(default_factory=utc_now)
