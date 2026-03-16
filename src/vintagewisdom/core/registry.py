from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..plugins.base import Plugin, PluginInfo


@dataclass
class PluginLoadError:
    name: str
    error: str


class PluginRegistry:
    def __init__(self, app: Any):
        self.app = app
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}

    def discover_from_package(self, package_name: str) -> List[PluginLoadError]:
        errors: List[PluginLoadError] = []
        try:
            package = importlib.import_module(package_name)
        except Exception as e:
            return [PluginLoadError(name=package_name, error=str(e))]

        for _, name, _ in pkgutil.iter_modules(getattr(package, "__path__", [])):
            mod_name = f"{package_name}.{name}"
            try:
                module = importlib.import_module(mod_name)
                self._load_from_module(module)
            except Exception as e:
                errors.append(PluginLoadError(name=mod_name, error=str(e)))
        return errors

    def discover_user_plugins(self, plugin_dir: Path) -> List[PluginLoadError]:
        errors: List[PluginLoadError] = []
        if not plugin_dir.exists() or not plugin_dir.is_dir():
            return errors

        import sys

        sys.path.insert(0, str(plugin_dir.parent))
        for item in plugin_dir.iterdir():
            if not item.is_dir():
                continue
            if not (item / "__init__.py").exists():
                continue
            try:
                module = importlib.import_module(f"{plugin_dir.name}.{item.name}")
                self._load_from_module(module)
            except Exception as e:
                errors.append(PluginLoadError(name=item.name, error=str(e)))
        return errors

    def _load_from_module(self, module: Any) -> None:
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if not isinstance(attr, type):
                continue
            if not issubclass(attr, Plugin) or attr is Plugin:
                continue
            info = getattr(attr, "INFO", None)
            if not isinstance(info, PluginInfo):
                continue
            self._plugin_classes[info.name] = attr

    def load(self, name: str, config: Optional[dict] = None) -> Plugin:
        if name in self._plugins:
            return self._plugins[name]
        if name not in self._plugin_classes:
            raise ValueError(f"Unknown plugin: {name}")
        cls = self._plugin_classes[name]
        plugin = cls(self.app, config or {})
        plugin.initialize()
        self._plugins[name] = plugin
        return plugin

    def unload(self, name: str) -> None:
        plugin = self._plugins.get(name)
        if not plugin:
            return
        try:
            plugin.deactivate()
        finally:
            self._plugins.pop(name, None)

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def list_available(self) -> List[PluginInfo]:
        return [cls.INFO for cls in self._plugin_classes.values()]

    def list_loaded(self) -> List[str]:
        return list(self._plugins.keys())
