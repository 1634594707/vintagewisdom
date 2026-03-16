from __future__ import annotations

from ..core.events import events
from .base import Plugin, PluginInfo, register_hook


class DemoPlugin(Plugin):
    INFO = PluginInfo(
        name="demo",
        version="0.1.0",
        description="Demo plugin for wiring verification",
        author="VintageWisdom",
        dependencies=[],
    )

    def initialize(self) -> None:
        events.on("app.initialized", self._on_app_initialized)

    @register_hook("app.initialized")
    def _on_app_initialized(self, event) -> None:
        return
