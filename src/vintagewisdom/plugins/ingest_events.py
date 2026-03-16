from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.ingest")


class IngestEventsPlugin(Plugin):
    INFO = PluginInfo(
        name="ingest.events",
        version="0.1.0",
        description="Observability hooks for ingest.* events",
        author="VintageWisdom",
        dependencies=[],
    )

    def initialize(self) -> None:
        events.on("ingest.started", self._on_started)
        events.on("ingest.completed", self._on_completed)
        events.on("ingest.failed", self._on_failed)

    def _on_started(self, event) -> None:
        return

    def _on_completed(self, event) -> None:
        return

    def _on_failed(self, event) -> None:
        return
