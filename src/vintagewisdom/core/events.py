from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class Event:
    name: str
    data: Dict[str, Any]
    timestamp: datetime


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, List[Callable[[Event], Any]]] = defaultdict(list)

    def on(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        self._handlers[event_name].append(handler)

    def off(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        if event_name not in self._handlers:
            return
        try:
            self._handlers[event_name].remove(handler)
        except ValueError:
            return

    def emit(self, event_name: str, data: Dict[str, Any] | None = None) -> None:
        event = Event(name=event_name, data=data or {}, timestamp=datetime.utcnow())
        for handler in list(self._handlers.get(event_name, [])):
            try:
                handler(event)
            except Exception:
                continue


events = EventBus()
