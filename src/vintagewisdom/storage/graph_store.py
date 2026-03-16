from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple


class GraphStore:
    def __init__(self) -> None:
        self._edges: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

    def add_edge(self, source: str, target: str, relation: str) -> None:
        self._edges[source].append((target, relation))

    def neighbors(self, node: str) -> List[Tuple[str, str]]:
        return list(self._edges.get(node, []))
