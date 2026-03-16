from __future__ import annotations

from typing import Any, Dict, Optional

from ..bias.detector import BiasDetector
from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.bias_detector")


class BiasDetectorPlugin(Plugin):
    INFO = PluginInfo(
        name="bias.detector",
        version="0.1.0",
        description="Detect cognitive bias signals and inject warnings into reasoning",
        author="VintageWisdom",
        dependencies=[],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)
        self._detector = BiasDetector()

    def initialize(self) -> None:
        events.on("decision.before", self._on_decision_before)
        events.on("decision.after", self._on_decision_after)

    def _on_decision_before(self, event) -> None:
        try:
            data = event.data or {}
            text = str(data.get("text") or "")
            biases = self._detector.detect(text)
            if biases:
                ctx = data.get("context")
                if isinstance(ctx, dict):
                    ctx["bias_warnings"] = biases
        except Exception:
            return

    def _on_decision_after(self, event) -> None:
        try:
            data = event.data or {}
            ctx = data.get("context")
            if not isinstance(ctx, dict):
                return
            biases = ctx.get("bias_warnings")
            if not isinstance(biases, list) or not biases:
                return
            reasoning = str(data.get("reasoning") or "")
            warn = ", ".join([str(x) for x in biases if str(x).strip()])
            if warn:
                data["reasoning"] = (reasoning + "\n\n[BiasWarnings]\n" + warn).strip()
        except Exception as e:
            log.error("bias.detector failed: %s", e)
            return
