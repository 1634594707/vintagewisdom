from __future__ import annotations

from typing import Any, Dict, Optional

from ..ai.redteam import RedTeam
from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.ai_redteam")


class AIRedTeamPlugin(Plugin):
    INFO = PluginInfo(
        name="ai.redteam",
        version="0.1.0",
        description="Red-team critique injected into decision reasoning",
        author="VintageWisdom",
        dependencies=[],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)
        self._redteam = RedTeam()

    def initialize(self) -> None:
        events.on("decision.after", self._on_decision_after)

    def _on_decision_after(self, event) -> None:
        try:
            data = event.data or {}
            text = str(data.get("text") or "")
            if not text.strip():
                return
            critique = self._redteam.run(text)
            if not critique:
                return
            reasoning = str(data.get("reasoning") or "")
            data["reasoning"] = (reasoning + "\n\n[RedTeam]\n" + critique).strip()
        except Exception as e:
            log.error("ai.redteam failed: %s", e)
            return
