from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.storage_sqlite")


class StorageSqlitePlugin(Plugin):
    INFO = PluginInfo(
        name="storage.sqlite",
        version="0.1.0",
        description="SQLite storage bootstrap (Database initialization)",
        author="VintageWisdom",
        dependencies=[],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)

    def initialize(self) -> None:
        try:
            self.app.engine.initialize()
        except Exception as e:
            log.error("storage.sqlite init failed: %s", e)
            return
        events.emit("storage.ready", {"backend": "sqlite", "path": str(getattr(self.app.engine.db, "path", ""))})
