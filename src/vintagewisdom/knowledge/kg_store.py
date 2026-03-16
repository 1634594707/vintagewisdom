from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import hashlib

from ..storage.database import Database
from ..utils.config import Config


_NEO4J_DRIVER_CACHE: Dict[Tuple[str, str, str], Any] = {}


def _neo_label_for_entity_type(entity_type: str) -> str:
    t = (entity_type or "").strip().lower()
    if t in {"crash", "market_crash", "股灾", "股灾名称", "事件", "crisis"}:
        return "Crash"
    if t in {"risk", "risk_type", "risk-type", "risktype", "风险", "风险类型"}:
        return "RiskType"
    if t in {"event", "事件", "trigger", "policy_event"}:
        return "Event"
    return "Entity"


def _neo_reltype_for_relation_type(relation_type: str) -> str:
    t = (relation_type or "").strip().lower()
    if t in {"has_risk_type", "risk_type", "风险类型", "belongs_to_risk", "is_risk_type"}:
        return "HAS_RISK_TYPE"
    if t in {"triggered_by", "trigger", "导火索", "caused_by_event"}:
        return "TRIGGERED_BY"
    if t in {"causes", "cause", "caused", "导致"}:
        return "CAUSED"
    if t in {"leads_to", "lead_to", "leads", "引发"}:
        return "LEADS_TO"
    if t in {"part_of", "belongs_to", "组成"}:
        return "PART_OF"
    if t in {"used_for", "用于"}:
        return "USED_FOR"
    return "RELATED_TO"


@dataclass
class KGSubgraph:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]


class KGStore:
    def upsert_entities(self, entities: List[Dict[str, Any]]) -> None:
        raise NotImplementedError

    def upsert_relations_with_evidence(self, relations: List[Dict[str, Any]]) -> None:
        raise NotImplementedError

    def query_subgraph(
        self,
        *,
        q: str = "",
        seed_entity_id: str = "",
        relation_type: str = "",
        depth: int = 1,
        max_entities: int = 300,
        max_relations: int = 600,
    ) -> KGSubgraph:
        raise NotImplementedError


class SqliteKGStore(KGStore):
    def __init__(self, db: Database):
        self.db = db

    def upsert_entities(self, entities: List[Dict[str, Any]]) -> None:
        for e in entities:
            self.db.upsert_entity(
                entity_id=str(e["id"]),
                name=str(e.get("name") or e.get("label") or e["id"]),
                entity_type=str(e.get("type") or "entity"),
                attributes=e.get("attributes") if isinstance(e.get("attributes"), dict) else {},
                updated_at=e.get("updated_at"),
            )

    def upsert_relations_with_evidence(self, relations: List[Dict[str, Any]]) -> None:
        for r in relations:
            rid = str(r["id"])
            self.db.upsert_relation(
                relation_id=rid,
                source_entity_id=str(r["source"]),
                target_entity_id=str(r["target"]),
                relation_type=str(r.get("relation_type") or r.get("type") or "related_to"),
                confidence=float(r.get("confidence") or 0.5),
                attributes=r.get("attributes") if isinstance(r.get("attributes"), dict) else {},
                updated_at=r.get("updated_at"),
            )
            quote = str(r.get("quote") or "")
            case_id = str(r.get("case_id") or "")
            if quote and case_id:
                ev_id = str(r.get("evidence_id") or f"ev_{rid}_{case_id}"[:64])
                self.db.add_relation_evidence(
                    evidence_id=ev_id,
                    relation_id=rid,
                    case_id=case_id,
                    quote=quote[:2000],
                    start_offset=None,
                    end_offset=None,
                    created_at=None,
                )

    def query_subgraph(
        self,
        *,
        q: str = "",
        seed_entity_id: str = "",
        relation_type: str = "",
        depth: int = 1,
        max_entities: int = 300,
        max_relations: int = 600,
    ) -> KGSubgraph:
        seed = (seed_entity_id or "").strip()
        query = (q or "").strip()
        rel_filter = (relation_type or "").strip().lower()

        depth = max(1, min(int(depth or 1), 3))

        if seed:
            seen_nodes = set([seed])
            frontier = set([seed])
            rel_rows: List[Dict[str, Any]] = []

            for _ in range(depth):
                if not frontier:
                    break
                rels = self.db.list_relations_for_entities(list(frontier), limit=max_relations)
                if rel_filter:
                    rels = [r for r in rels if str(r.get("relation_type") or "").lower() == rel_filter]
                rel_rows.extend(rels)
                next_frontier: set[str] = set()
                for r in rels:
                    s = r.get("source_entity_id") or ""
                    t = r.get("target_entity_id") or ""
                    if s and s not in seen_nodes:
                        next_frontier.add(s)
                    if t and t not in seen_nodes:
                        next_frontier.add(t)
                seen_nodes |= next_frontier
                frontier = next_frontier
                if len(seen_nodes) >= max_entities:
                    break

            # cap
            seen_list = list(seen_nodes)[: int(max_entities)]
            entities = self.db.get_entities_by_ids(seen_list)
            relations = rel_rows[: int(max_relations)]
        elif query:
            entities = self.db.search_entities(query, limit=max_entities)
            entity_ids = [e.get("id") for e in entities if e.get("id")]
            relations = self.db.list_relations_for_entities(entity_ids, limit=max_relations)
            if rel_filter:
                relations = [r for r in relations if str(r.get("relation_type") or "").lower() == rel_filter]
        else:
            entities = self.db.list_entities(limit=max_entities)
            entity_ids = [e.get("id") for e in entities if e.get("id")]
            relations = self.db.list_relations_for_entities(entity_ids, limit=max_relations)
            if rel_filter:
                relations = [r for r in relations if str(r.get("relation_type") or "").lower() == rel_filter]

        rel_ids = [r.get("id") for r in relations if r.get("id")]
        evidence = self.db.list_relation_evidence(rel_ids, limit=2000)
        evidence_by_rel: Dict[str, List[Dict[str, Any]]] = {}
        for ev in evidence:
            rid = ev.get("relation_id")
            if not rid:
                continue
            evidence_by_rel.setdefault(rid, []).append(ev)

        nodes: List[Dict[str, Any]] = []
        for e in entities:
            nodes.append(
                {
                    "id": e.get("id"),
                    "type": e.get("type") or "entity",
                    "label": e.get("name") or e.get("id"),
                    "attributes": e.get("attributes") or {},
                }
            )

        edges: List[Dict[str, Any]] = []
        for r in relations:
            rid = r.get("id")
            edges.append(
                {
                    "id": rid,
                    "source": r.get("source_entity_id"),
                    "target": r.get("target_entity_id"),
                    "type": r.get("relation_type"),
                    "edge_type": r.get("relation_type"),
                    "confidence": r.get("confidence"),
                    "attributes": r.get("attributes") or {},
                    "evidence": evidence_by_rel.get(rid or "", []) if rid else [],
                }
            )

        # Aggregate parallel relations into a single display edge per (source,target)
        # Strategy C: strength = 1 - Π(1 - conf_i)
        try:
            agg: Dict[Tuple[str, str], Dict[str, Any]] = {}
            for e in edges:
                s = str(e.get("source") or "").strip()
                t = str(e.get("target") or "").strip()
                if not s or not t:
                    continue
                key = (s, t)
                try:
                    c = float(e.get("confidence") or 0.0)
                except Exception:
                    c = 0.0
                c = max(0.0, min(1.0, c))
                rt = str(e.get("edge_type") or e.get("type") or "RELATED_TO")
                ev = e.get("evidence") if isinstance(e.get("evidence"), list) else []

                if key not in agg:
                    base_attr = e.get("attributes") if isinstance(e.get("attributes"), dict) else {}
                    agg[key] = {
                        "id": "",  # set later
                        "source": s,
                        "target": t,
                        "type": "RELATED_TO",
                        "edge_type": "RELATED_TO",
                        "confidence": c,
                        "strength": c,
                        "attributes": {
                            **base_attr,
                            "relation_types": [rt],
                            "relation_count": 1,
                        },
                        "evidence": list(ev),
                        "_prod": (1.0 - c),
                    }
                else:
                    a = agg[key]
                    a["_prod"] = float(a.get("_prod") or 1.0) * (1.0 - c)
                    a["strength"] = 1.0 - float(a["_prod"])
                    a["confidence"] = float(a["strength"])  # keep compatibility
                    try:
                        attrs = a.get("attributes") if isinstance(a.get("attributes"), dict) else {}
                        rts = attrs.get("relation_types")
                        if not isinstance(rts, list):
                            rts = []
                        if rt not in rts:
                            rts.append(rt)
                        attrs["relation_types"] = rts
                        attrs["relation_count"] = int(attrs.get("relation_count") or 0) + 1
                        a["attributes"] = attrs
                    except Exception:
                        pass
                    try:
                        if ev:
                            a_ev = a.get("evidence") if isinstance(a.get("evidence"), list) else []
                            a_ev.extend(ev)
                            a["evidence"] = a_ev
                    except Exception:
                        pass

            out_edges: List[Dict[str, Any]] = []
            for (s, t), a in agg.items():
                # stable id
                h = hashlib.sha1(f"{s}->{t}".encode("utf-8")).hexdigest()[:16]
                a["id"] = f"agg_{h}"
                a.pop("_prod", None)
                out_edges.append(a)
            edges = out_edges
        except Exception:
            pass

        return KGSubgraph(
            nodes=nodes,
            edges=edges,
            stats={
                "entity_count": len(nodes),
                "relation_count": len(edges),
                "evidence_count": len(evidence),
            },
        )


class Neo4jKGStore(KGStore):
    def __init__(self, *, uri: str, user: str, password: str, database: str = "neo4j"):
        try:
            from neo4j import GraphDatabase  # type: ignore
        except Exception as e:
            raise RuntimeError("Neo4j dependency not installed. Install with: pip install -e '.[kg]' ") from e

        global _NEO4J_DRIVER_CACHE
        key = (str(uri), str(user), str(database))
        driver = _NEO4J_DRIVER_CACHE.get(key)
        if driver is None:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            _NEO4J_DRIVER_CACHE[key] = driver

        self._driver = driver
        self._database = database
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cypher = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",

            "CREATE CONSTRAINT crash_id IF NOT EXISTS FOR (e:Crash) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX crash_name IF NOT EXISTS FOR (e:Crash) ON (e.name)",

            "CREATE CONSTRAINT risk_type_id IF NOT EXISTS FOR (e:RiskType) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX risk_type_name IF NOT EXISTS FOR (e:RiskType) ON (e.name)",

            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE INDEX event_name IF NOT EXISTS FOR (e:Event) ON (e.name)",

            # keep legacy constraint for previous REL model if graph already contains it
            "CREATE CONSTRAINT rel_id IF NOT EXISTS FOR ()-[r:REL]-() REQUIRE r.id IS UNIQUE",
        ]
        with self._driver.session(database=self._database) as s:
            for q in cypher:
                try:
                    s.run(q)
                except Exception:
                    pass

    def close(self) -> None:
        # Driver is shared via module-level cache; do not close here.
        return None

    def upsert_entities(self, entities: List[Dict[str, Any]]) -> None:
        now = datetime.utcnow().isoformat()
        by_label: Dict[str, List[Dict[str, Any]]] = {}
        for e in entities:
            label = _neo_label_for_entity_type(str(e.get("type") or ""))
            by_label.setdefault(label, []).append(
                {
                    "id": str(e["id"]),
                    "name": str(e.get("name") or e.get("label") or e["id"]),
                    "type": str(e.get("type") or "entity"),
                    "attributes": json.dumps(e.get("attributes") or {}, ensure_ascii=False),
                    "updated_at": now,
                }
            )

        if not by_label:
            return

        with self._driver.session(database=self._database) as s:
            for label, rows in by_label.items():
                if not rows:
                    continue
                s.run(
                    f"""
                    UNWIND $rows AS row
                    MERGE (e:{label} {{id: row.id}})
                    SET e.name = row.name,
                        e.type = row.type,
                        e.attributes = row.attributes,
                        e.updated_at = row.updated_at
                    """,
                    rows=rows,
                )

    def upsert_relations_with_evidence(self, relations: List[Dict[str, Any]]) -> None:
        now = datetime.utcnow().isoformat()
        by_reltype: Dict[str, List[Dict[str, Any]]] = {}
        for r in relations:
            rid = str(r["id"])
            rt = _neo_reltype_for_relation_type(str(r.get("relation_type") or r.get("type") or ""))
            by_reltype.setdefault(rt, []).append(
                {
                    "id": rid,
                    "source": str(r["source"]),
                    "target": str(r["target"]),
                    "confidence": float(r.get("confidence") or 0.5),
                    "attributes": json.dumps(r.get("attributes") or {}, ensure_ascii=False),
                    "case_id": str(r.get("case_id") or ""),
                    "quote": str(r.get("quote") or ""),
                    "updated_at": now,
                }
            )

        if not by_reltype:
            return

        with self._driver.session(database=self._database) as s:
            for reltype, rows in by_reltype.items():
                if not rows:
                    continue
                s.run(
                    f"""
                    UNWIND $rows AS row
                    MATCH (src {{id: row.source}})
                    MATCH (tgt {{id: row.target}})
                    MERGE (src)-[rel:{reltype} {{id: row.id}}]->(tgt)
                    SET rel.confidence = row.confidence,
                        rel.attributes = row.attributes,
                        rel.updated_at = row.updated_at
                    WITH rel, row
                    FOREACH (_ IN CASE WHEN row.quote <> '' AND row.case_id <> '' THEN [1] ELSE [] END |
                      MERGE (ev:Evidence {id: row.id + '::' + row.case_id})
                      SET ev.case_id = row.case_id,
                          ev.quote = row.quote,
                          ev.updated_at = row.updated_at
                      MERGE (rel)-[:HAS_EVIDENCE]->(ev)
                    )
                    """,
                    rows=rows,
                )

    def query_subgraph(
        self,
        *,
        q: str = "",
        seed_entity_id: str = "",
        relation_type: str = "",
        depth: int = 1,
        max_entities: int = 300,
        max_relations: int = 600,
    ) -> KGSubgraph:
        seed = (seed_entity_id or "").strip()
        query = (q or "").strip()

        depth = max(1, min(int(depth or 1), 3))
        rel_filter = (relation_type or "").strip().lower()

        with self._driver.session(database=self._database) as s:
            if seed:
                result = s.run(
                    """
                    MATCH p=(s {id: $seed})-[rs*1..$depth]-(n)
                    WHERE (s:Crash OR s:RiskType OR s:Event OR s:Entity)
                      AND (n:Crash OR n:RiskType OR n:Event OR n:Entity)
                    UNWIND rs AS rel
                    WITH collect(distinct s) + collect(distinct n) AS nodes, collect(distinct rel) AS rels
                    RETURN
                      [x IN nodes | {id: x.id, name: x.name, type: coalesce(x.type, head(labels(x)))}] AS nodes,
                      [r IN rels | {id: r.id, type: type(r), confidence: r.confidence, source: startNode(r).id, target: endNode(r).id}] AS rels
                    """,
                    seed=seed,
                    depth=int(depth),
                ).single()
                entity_nodes = result["nodes"] if result else []
                rels = result["rels"] if result else []
            elif query:
                result = s.run(
                    """
                    MATCH (e)
                    WHERE (e:Crash OR e:RiskType OR e:Event OR e:Entity)
                      AND e.name CONTAINS $q
                    WITH e LIMIT $limit
                    OPTIONAL MATCH (e)-[r]-(n)
                    WHERE (n:Crash OR n:RiskType OR n:Event OR n:Entity)
                    RETURN
                      collect(distinct {id: e.id, name: e.name, type: coalesce(e.type, head(labels(e)))}) AS seeds,
                      collect(distinct {id: r.id, type: type(r), confidence: r.confidence, source: startNode(r).id, target: endNode(r).id}) AS rels,
                      collect(distinct {id: n.id, name: n.name, type: coalesce(n.type, head(labels(n)))}) AS nodes
                    """,
                    q=query,
                    limit=int(max_entities),
                ).single()
                seeds = result["seeds"] if result else []
                rels = result["rels"] if result else []
                nodes = result["nodes"] if result else []
                entity_nodes = list({n["id"]: n for n in (seeds + nodes) if n}.values())
            else:
                result = s.run(
                    """
                    MATCH (e)
                    WHERE (e:Crash OR e:RiskType OR e:Event OR e:Entity)
                    WITH e ORDER BY e.updated_at DESC LIMIT $limit
                    OPTIONAL MATCH (e)-[r]-(n)
                    WHERE (n:Crash OR n:RiskType OR n:Event OR n:Entity)
                    RETURN
                      collect(distinct {id: e.id, name: e.name, type: coalesce(e.type, head(labels(e)))}) AS seeds,
                      collect(distinct {id: r.id, type: type(r), confidence: r.confidence, source: startNode(r).id, target: endNode(r).id}) AS rels,
                      collect(distinct {id: n.id, name: n.name, type: coalesce(n.type, head(labels(n)))}) AS nodes
                    """,
                    limit=int(max_entities),
                ).single()
                seeds = result["seeds"] if result else []
                rels = result["rels"] if result else []
                nodes = result["nodes"] if result else []
                entity_nodes = list({n["id"]: n for n in (seeds + nodes) if n}.values())

            # cap nodes/relations
            if entity_nodes:
                dedup = {}
                for n in entity_nodes:
                    if not n:
                        continue
                    dedup[n.get("id")] = n
                entity_nodes = list(dedup.values())[: int(max_entities)]

            rels = [r for r in rels if r]
            if rel_filter:
                rels = [r for r in rels if str(r.get("type") or "").lower() == rel_filter]
            rels = rels[: int(max_relations)]

            # collect evidence
            rel_ids = [r["id"] for r in rels if r and r.get("id")]
            evidence_by_rel: Dict[str, List[Dict[str, Any]]] = {}
            if rel_ids:
                ev_rows = s.run(
                    """
                    UNWIND $rel_ids AS rid
                    MATCH ()-[rel:REL {id: rid}]-()-[:HAS_EVIDENCE]->(ev:Evidence)
                    RETURN rid AS rid, ev.id AS id, ev.case_id AS case_id, substring(ev.quote, 0, 240) AS quote, ev.updated_at AS created_at
                    """,
                    rel_ids=rel_ids,
                ).data()
                for row in ev_rows:
                    evidence_by_rel.setdefault(row["rid"], []).append(
                        {
                            "id": row.get("id"),
                            "relation_id": row.get("rid"),
                            "case_id": row.get("case_id"),
                            "quote": row.get("quote"),
                            "created_at": row.get("created_at"),
                        }
                    )

        nodes_out: List[Dict[str, Any]] = []
        for n in entity_nodes:
            if not n:
                continue
            nodes_out.append(
                {
                    "id": n.get("id"),
                    "type": n.get("type") or "entity",
                    "label": n.get("name") or n.get("id"),
                    "attributes": {},
                }
            )

        edges_out: List[Dict[str, Any]] = []
        for r in rels:
            if not r:
                continue
            rid = r.get("id")
            edges_out.append(
                {
                    "id": rid,
                    "source": r.get("source"),
                    "target": r.get("target"),
                    "type": r.get("type"),
                    "edge_type": r.get("type"),
                    "confidence": r.get("confidence"),
                    "attributes": {},
                    "evidence": evidence_by_rel.get(rid or "", []) if rid else [],
                }
            )

        evidence_count = sum(len(v) for v in evidence_by_rel.values())
        return KGSubgraph(
            nodes=nodes_out,
            edges=[e for e in edges_out if e.get("source") and e.get("target")],
            stats={
                "entity_count": len(nodes_out),
                "relation_count": len(edges_out),
                "evidence_count": evidence_count,
            },
        )


class KGCache:
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        return None

    def invalidate_prefix(self, prefix: str) -> None:
        return None


class RedisKGCache(KGCache):
    def __init__(self, url: str):
        try:
            import redis  # type: ignore
        except Exception as e:
            raise RuntimeError("Redis dependency not installed. Install with: pip install -e '.[kg]' ") from e

        self._r = redis.Redis.from_url(url)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            raw = self._r.get(key)
            if not raw:
                return None
            try:
                return json.loads(raw)
            except Exception:
                return None
        except Exception:
            return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
        try:
            self._r.setex(key, int(ttl_seconds), json.dumps(value, ensure_ascii=False))
        except Exception:
            return None

    def invalidate_prefix(self, prefix: str) -> None:
        # best-effort scan
        try:
            for k in self._r.scan_iter(match=f"{prefix}*"):
                self._r.delete(k)
        except Exception:
            pass


def get_kg_store(config: Config, db: Database) -> KGStore:
    store = str(config.get("kg.store", "sqlite") or "sqlite").lower()
    if store == "neo4j":
        neo = config.get("kg.neo4j", {}) or {}
        return Neo4jKGStore(
            uri=str(neo.get("uri") or "bolt://127.0.0.1:7687"),
            user=str(neo.get("user") or "neo4j"),
            password=str(neo.get("password") or ""),
            database=str(neo.get("database") or "neo4j"),
        )
    return SqliteKGStore(db)


def get_kg_cache(config: Config) -> Tuple[KGCache, int]:
    redis_cfg = config.get("kg.redis", {}) or {}
    url = str(redis_cfg.get("url") or "").strip()
    ttl = int(redis_cfg.get("ttl_seconds") or 300)
    if not url:
        return KGCache(), ttl
    try:
        return RedisKGCache(url), ttl
    except Exception:
        return KGCache(), ttl
