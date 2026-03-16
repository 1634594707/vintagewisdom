from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.ai_classify")


class AIClassifyPlugin(Plugin):
    INFO = PluginInfo(
        name="ai.classify",
        version="0.1.0",
        description="Auto classify case domain/tags after insertion (accuracy-first)",
        author="VintageWisdom",
        dependencies=[],
    )

    def initialize(self) -> None:
        events.on("case.added", self._on_case_added)

    def _on_case_added(self, event) -> None:
        try:
            case = event.data.get("case")
            if not case:
                return

            dom = str(getattr(case, "domain", "") or "").strip()
            if dom and dom.upper() not in {"GENERAL", "GEN", "UNKNOWN"}:
                return

            engine = self.app.engine
            try:
                if not getattr(engine, "ai_assistant", None) or not engine.ai_assistant.check_available():
                    return
            except Exception:
                return

            try:
                from ..knowledge.domains import auto_classify_domain
            except Exception:
                return

            text = "\n".join(
                [
                    getattr(case, "title", "") or "",
                    getattr(case, "description", "") or "",
                    getattr(case, "decision_node", "") or "",
                ]
            ).strip()
            if not text:
                return

            results = auto_classify_domain(text)
            if not results:
                return

            top = results[0]
            try:
                conf = float(top.get("confidence") or 0.0)
            except Exception:
                conf = 0.0
            if conf < 0.6:
                return

            new_dom = str(top.get("domain") or "").strip()
            if not new_dom:
                return

            # Refresh latest row from DB to avoid stale object mutation
            c = engine.db.get_case(str(getattr(case, "id", "")))
            c.domain = new_dom
            try:
                c.domain_tags = json.dumps(results[:3], ensure_ascii=False)
            except Exception:
                c.domain_tags = None

            # Persist without calling engine.add_case() to avoid re-emitting case.added
            engine.db.insert_case(c)
            events.emit("case.updated", {"case": c, "source": "ai.classify"})
        except Exception as e:
            log.error("AI classify plugin failed: %s", e)
            return
