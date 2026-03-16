from __future__ import annotations

from typing import Dict


class DomainMappings:
    def __init__(self) -> None:
        self._mappings: Dict[str, dict] = {}

    def add_mapping(self, name: str, data: dict) -> None:
        self._mappings[name] = data
