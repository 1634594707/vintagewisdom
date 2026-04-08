from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.evidence_builder")


def build_evidence(
    *,
    text: str,
    cases: List[Any],
    engine: Any,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = config or {}
    max_cases = int(cfg.get("max_cases", 5) or 5)
    max_snippets = int(cfg.get("max_snippets", 8) or 8)
    snippet_chars = int(cfg.get("snippet_chars", 240) or 240)

    trimmed_cases = [c for c in cases if c is not None][:max_cases]

    evidence_cases: List[Dict[str, Any]] = []
    snippets: List[Dict[str, Any]] = []

    for case in trimmed_cases:
        try:
            evidence_cases.append(
                {
                    "id": getattr(case, "id", ""),
                    "title": getattr(case, "title", ""),
                    "domain": getattr(case, "domain", ""),
                    "lesson_core": getattr(case, "lesson_core", None),
                    "outcome_result": getattr(case, "outcome_result", None),
                }
            )
        except Exception:
            continue

        if len(snippets) >= max_snippets:
            continue
        snippet = _select_snippet(case, snippet_chars)
        if snippet:
            snippets.append(
                {
                    "case_id": getattr(case, "id", ""),
                    "field": snippet.get("field"),
                    "text": snippet.get("text"),
                }
            )

    kg_paths = _build_kg_paths(
        text=text,
        case_ids=[str(c.get("id") or "") for c in evidence_cases if isinstance(c, dict)],
        engine=engine,
        config=cfg.get("kg") if isinstance(cfg.get("kg"), dict) else {},
    )

    return {
        "cases": evidence_cases,
        "snippets": snippets,
        "kg_paths": kg_paths,
    }


def _select_snippet(case: Any, snippet_chars: int) -> Optional[Dict[str, str]]:
    fields = [
        ("description", getattr(case, "description", None)),
        ("lesson_core", getattr(case, "lesson_core", None)),
        ("action_taken", getattr(case, "action_taken", None)),
        ("outcome_result", getattr(case, "outcome_result", None)),
    ]
    for name, value in fields:
        text = (value or "").strip()
        if text:
            return {"field": name, "text": text[:snippet_chars]}
    return None


def _build_kg_paths(
    *,
    text: str,
    case_ids: List[str],
    engine: Any,
    config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    cfg = config or {}
    enabled = bool(cfg.get("enabled", True))
    if not enabled or engine is None:
        return []

    try:
        from ..knowledge.kg_store import get_kg_store
    except Exception:
        return []

    depth = int(cfg.get("depth", 1) or 1)
    max_paths = int(cfg.get("max_paths", 6) or 6)
    max_entities = int(cfg.get("max_entities", 120) or 120)
    max_relations = int(cfg.get("max_relations", 200) or 200)

    try:
        store = get_kg_store(engine.config, engine.db)
        subgraph = store.query_subgraph(
            q=text[:200],
            depth=depth,
            max_entities=max_entities,
            max_relations=max_relations,
        )
    except Exception:
        return []

    node_labels = {n.get("id"): n.get("label") for n in (subgraph.nodes or []) if isinstance(n, dict)}

    case_set = {cid for cid in case_ids if cid}
    paths: List[Dict[str, Any]] = []

    for edge in subgraph.edges or []:
        if len(paths) >= max_paths:
            break
        if not isinstance(edge, dict):
            continue
        src = edge.get("source")
        tgt = edge.get("target")
        if not src or not tgt:
            continue
        evs = edge.get("evidence")
        ev_list = evs if isinstance(evs, list) else []
        if case_set:
            ev_list = [ev for ev in ev_list if isinstance(ev, dict) and ev.get("case_id") in case_set]
        if case_set and not ev_list:
            continue
        path_text = f"{node_labels.get(src, src)} -[{edge.get('type') or edge.get('edge_type') or 'RELATED_TO'}]-> {node_labels.get(tgt, tgt)}"
        paths.append(
            {
                "path": path_text,
                "edge_type": edge.get("type") or edge.get("edge_type"),
                "evidence": [
                    {
                        "case_id": ev.get("case_id"),
                        "quote": ev.get("quote"),
                    }
                    for ev in ev_list[:3]
                    if isinstance(ev, dict)
                ],
            }
        )

    return paths


class EvidenceBuilderPlugin(Plugin):
    INFO = PluginInfo(
        name="evidence.builder",
        version="0.1.0",
        description="Build structured evidence bundle for downstream AI plugins",
        author="VintageWisdom",
        dependencies=[],
    )

    def initialize(self) -> None:
        events.on("decision.after", self._on_decision_after)

    def _on_decision_after(self, event) -> None:
        try:
            data = event.data or {}
            if isinstance(data.get("evidence"), dict):
                return
            text = str(data.get("text") or "")
            cases = data.get("cases")
            if not isinstance(cases, list):
                cases = []
            evidence = build_evidence(
                text=text,
                cases=cases,
                engine=getattr(self.app, "engine", None),
                config=self.config,
            )
            data["evidence"] = evidence
        except Exception as e:
            log.error("evidence.builder failed: %s", e)
            return
