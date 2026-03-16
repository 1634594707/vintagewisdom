from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HotIndexItem:
    id: str
    name: str
    count: int


class HotIndex:
    def __init__(self, *, kg_store: Any):
        self._kg_store = kg_store
        self._risk_types: List[HotIndexItem] = []
        self._events: List[HotIndexItem] = []
        self._risk_type_by_name: Dict[str, str] = {}
        self._crash_by_name: Dict[str, str] = {}
        self._event_by_name: Dict[str, str] = {}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "risk_types": [i.__dict__ for i in self._risk_types],
            "events": [i.__dict__ for i in self._events],
        }

    def match_ids(self, *, query: str, max_hits: int = 6) -> List[str]:
        q = (query or "").strip().lower()
        if not q:
            return []
        max_hits = max(1, min(int(max_hits or 6), 20))

        hits: List[str] = []

        # exact-ish hits first
        for m in (self._crash_by_name, self._risk_type_by_name, self._event_by_name):
            for name, eid in m.items():
                if not name or not eid:
                    continue
                if name in q or q in name:
                    hits.append(eid)
                    if len(hits) >= max_hits:
                        return hits

        # substring fallback (bounded)
        for m in (self._risk_type_by_name, self._event_by_name):
            for name, eid in list(m.items())[:2000]:
                if name and eid and name in q:
                    hits.append(eid)
                    if len(hits) >= max_hits:
                        return hits

        return hits

    def lookup(self, *, kind: str, name: str) -> Optional[str]:
        n = (name or "").strip().lower()
        if not n:
            return None
        k = (kind or "").strip().lower()
        if k in {"risk", "risk_type", "risktype"}:
            return self._risk_type_by_name.get(n)
        if k in {"crash"}:
            return self._crash_by_name.get(n)
        if k in {"event"}:
            return self._event_by_name.get(n)
        return None

    def refresh(self, *, limit: int = 50, scan_limit: int = 3000) -> None:
        store_name = self._kg_store.__class__.__name__
        if store_name != "Neo4jKGStore":
            return

        try:
            with self._kg_store._driver.session(database=self._kg_store._database) as s:  # type: ignore[attr-defined]
                risk_rows = s.run(
                    """
                    MATCH (r:RiskType)<-[:HAS_RISK_TYPE]-(:Crash)
                    RETURN r.id AS id, r.name AS name, count(*) AS c
                    ORDER BY c DESC
                    LIMIT $limit
                    """,
                    limit=int(limit),
                ).data()

                event_rows = s.run(
                    """
                    MATCH (e:Event)<-[:TRIGGERED_BY]-(:Crash)
                    RETURN e.id AS id, e.name AS name, count(*) AS c
                    ORDER BY c DESC
                    LIMIT $limit
                    """,
                    limit=int(limit),
                ).data()

                crash_rows = s.run(
                    """
                    MATCH (c:Crash)
                    RETURN c.id AS id, c.name AS name
                    LIMIT $scan
                    """,
                    scan=int(scan_limit),
                ).data()

                risk_rows2 = s.run(
                    """
                    MATCH (r:RiskType)
                    RETURN r.id AS id, r.name AS name
                    LIMIT $scan
                    """,
                    scan=int(scan_limit),
                ).data()

                event_rows2 = s.run(
                    """
                    MATCH (e:Event)
                    RETURN e.id AS id, e.name AS name
                    LIMIT $scan
                    """,
                    scan=int(scan_limit),
                ).data()
        except Exception:
            return

        self._risk_types = [HotIndexItem(id=str(r.get("id") or ""), name=str(r.get("name") or ""), count=int(r.get("c") or 0)) for r in risk_rows if r.get("id")]
        self._events = [HotIndexItem(id=str(r.get("id") or ""), name=str(r.get("name") or ""), count=int(r.get("c") or 0)) for r in event_rows if r.get("id")]

        self._crash_by_name = {str(r.get("name") or "").strip().lower(): str(r.get("id")) for r in crash_rows if r.get("id") and r.get("name")}
        self._risk_type_by_name = {str(r.get("name") or "").strip().lower(): str(r.get("id")) for r in risk_rows2 if r.get("id") and r.get("name")}
        self._event_by_name = {str(r.get("name") or "").strip().lower(): str(r.get("id")) for r in event_rows2 if r.get("id") and r.get("name")}
