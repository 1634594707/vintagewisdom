from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.config import Config
from .engine import Engine
from .events import events
from .registry import PluginRegistry


class VintageWisdomApp:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.engine = Engine(config=self.config)
        self.plugins = PluginRegistry(self)
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        self.engine.initialize()

        errors: list[dict[str, Any]] = []

        # 1) Discover built-in plugins
        try:
            errs = self.plugins.discover_from_package("vintagewisdom.plugins")
            errors.extend([e.__dict__ for e in (errs or [])])
        except Exception as e:
            errors.append({"name": "vintagewisdom.plugins", "error": str(e)})

        # 2) Discover user plugins
        user_dir = self.config.get("plugins.user_dir", "")
        if isinstance(user_dir, str) and user_dir.strip():
            try:
                errs = self.plugins.discover_user_plugins(Path(user_dir))
                errors.extend([e.__dict__ for e in (errs or [])])
            except Exception as e:
                errors.append({"name": str(user_dir), "error": str(e)})

        # 3) Determine what to load
        enabled = self.config.get("plugins.enabled", []) or []
        if not isinstance(enabled, list):
            enabled = []
        disabled = self.config.get("plugins.disabled", []) or []
        if not isinstance(disabled, list):
            disabled = []
        disabled_set = {str(x) for x in disabled if str(x).strip()}

        # Backward compatibility: if enabled list is non-empty, treat it as allowlist.
        if enabled:
            to_load = [str(x) for x in enabled if str(x).strip()]
        else:
            to_load = [info.name for info in self.plugins.list_available()]

        # Apply blacklist
        to_load = [n for n in to_load if n not in disabled_set]

        for name in to_load:
            try:
                cfg = self.config.get(f"plugins.config.{name}", {}) or {}
                self.plugins.load(str(name), cfg if isinstance(cfg, dict) else {})
            except Exception as e:
                errors.append({"name": str(name), "error": str(e)})

        events.emit("app.initialized", {"app": self, "errors": errors, "loaded": self.plugins.list_loaded()})
        self._initialized = True

    def shutdown(self) -> None:
        events.emit("app.shutdown", {"app": self})
        try:
            self.engine.db.close()
        except Exception:
            pass
