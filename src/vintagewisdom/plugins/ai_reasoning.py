from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.ai_reasoning")


class AIReasoningPlugin(Plugin):
    INFO = PluginInfo(
        name="ai.reasoning",
        version="0.1.0",
        description="Lightweight causal/structured reasoning augmentation",
        author="VintageWisdom",
        dependencies=["nlp.basic"],
    )

    def initialize(self) -> None:
        events.on("decision.after", self._on_decision_after)

    def _on_decision_after(self, event) -> None:
        try:
            data = event.data or {}
            text = str(data.get("text") or "")
            if not text.strip():
                return

            causal = None
            try:
                causal = getattr(self.app, "nlp", {}).get("causal")
            except Exception:
                causal = None

            chains = []
            if causal is not None:
                try:
                    chains = causal.extract(text)
                except Exception:
                    chains = []

            if not chains:
                return

            reasoning = str(data.get("reasoning") or "")
            extra = "\n".join([f"- {c}" for c in chains[:5] if str(c).strip()])
            if not extra.strip():
                return
            data["reasoning"] = (reasoning + "\n\n[Reasoning]\n" + extra).strip()
        except Exception as e:
            log.error("ai.reasoning failed: %s", e)
            return
