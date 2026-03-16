from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = field(default_factory=list)


class Plugin(ABC):
    INFO: PluginInfo

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        self.app = app
        self.config: Dict[str, Any] = config or {}
        self.enabled = True

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    def activate(self) -> None:
        self.enabled = True
        self.on_activate()

    def deactivate(self) -> None:
        self.enabled = False
        self.on_deactivate()

    def on_activate(self) -> None:
        return

    def on_deactivate(self) -> None:
        return

    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)


def register_command(name: str, help_text: str = ""):
    def decorator(func: Callable[..., Any]):
        setattr(func, "_is_command", True)
        setattr(func, "_command_name", name)
        setattr(func, "_help_text", help_text)
        return func

    return decorator


def register_hook(event_name: str, priority: int = 10):
    def decorator(func: Callable[..., Any]):
        setattr(func, "_is_hook", True)
        setattr(func, "_hook_event", event_name)
        setattr(func, "_hook_priority", int(priority))
        return func

    return decorator
