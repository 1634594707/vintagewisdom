from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.search_basic")


class SearchBasicPlugin(Plugin):
    INFO = PluginInfo(
        name="search.basic",
        version="0.1.0",
        description="Basic retrieval backend (wraps core.Retriever)",
        author="VintageWisdom",
        dependencies=["storage.sqlite"],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)

    def initialize(self) -> None:
        try:
            _ = self.app.engine.retriever
        except Exception as e:
            log.error("search.basic init failed: %s", e)
            return
        events.emit("search.ready", {"name": "basic"})
