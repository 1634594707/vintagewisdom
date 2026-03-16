from __future__ import annotations

import hashlib
import threading
from typing import Any, Dict, List, Optional

from ..core.events import events
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.kg_extract")


class KGExtractPlugin(Plugin):
    INFO = PluginInfo(
        name="kg.extract",
        version="0.1.0",
        description="Background knowledge graph extraction on case events",
        author="VintageWisdom",
        dependencies=[],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)
        self._kg_store = None
        self._kg_cache = None
        self._hot_index = None
        self._cache_ttl = 0

    def initialize(self) -> None:
        events.on("case.added", self._on_case_added)
        events.on("ingest.completed", self._on_ingest_completed)
        events.on("kg.extract.requested", self._on_extract_requested)

    def _ensure_runtime(self) -> bool:
        if self._kg_store is not None:
            return True
        try:
            engine = self.app.engine
            from ..knowledge.kg_store import get_kg_cache, get_kg_store
            from ..knowledge.hot_index import HotIndex

            self._kg_store = get_kg_store(engine.config, engine.db)
            self._kg_cache, self._cache_ttl = get_kg_cache(engine.config)
            self._hot_index = HotIndex(kg_store=self._kg_store)
            try:
                self._hot_index.refresh(limit=50)
            except Exception:
                pass
            return True
        except Exception as e:
            log.error("KG runtime init failed: %s", e)
            self._kg_store = None
            return False

    def _on_case_added(self, event) -> None:
        try:
            case = event.data.get("case")
            if not case:
                return
            engine = self.app.engine
            try:
                if not getattr(engine, "ai_assistant", None) or not engine.ai_assistant.check_available():
                    return
            except Exception:
                return

            if not self._ensure_runtime():
                return

            case_id = getattr(case, "id", None)
            if not case_id:
                return

            t = threading.Thread(target=self._worker, args=(str(case_id),), daemon=True)
            t.start()
        except Exception:
            return

    def _on_ingest_completed(self, event) -> None:
        try:
            data = event.data or {}
            case_ids = data.get("case_ids")
            if not isinstance(case_ids, list) or not case_ids:
                return
            self._schedule_many([str(x) for x in case_ids if str(x).strip()])
        except Exception:
            return

    def _on_extract_requested(self, event) -> None:
        try:
            data = event.data or {}
            case_ids = data.get("case_ids")
            if not isinstance(case_ids, list) or not case_ids:
                return
            self._schedule_many([str(x) for x in case_ids if str(x).strip()])
        except Exception:
            return

    def _schedule_many(self, case_ids: List[str]) -> None:
        if not case_ids:
            return
        engine = self.app.engine
        try:
            if not getattr(engine, "ai_assistant", None) or not engine.ai_assistant.check_available():
                return
        except Exception:
            return
        if not self._ensure_runtime():
            return
        for cid in case_ids:
            if not cid:
                continue
            t = threading.Thread(target=self._worker, args=(cid,), daemon=True)
            t.start()

    def _worker(self, case_id: str) -> None:
        try:
            engine = self.app.engine
            try:
                c = engine.db.get_case(case_id)
            except Exception:
                return

            text = "\n".join(
                [
                    c.title or "",
                    c.description or "",
                    c.decision_node or "",
                    c.action_taken or "",
                    c.outcome_result or "",
                    c.lesson_core or "",
                ]
            ).strip()
            if not text:
                return

            sha1 = hashlib.sha1(text.encode("utf-8")).hexdigest()
            try:
                state = engine.db.get_kg_case_state(c.id)
                if state and state.get("text_sha1") == sha1:
                    return
            except Exception:
                pass

            try:
                from ..knowledge.kg_extractor import extract_kg_from_case
            except Exception:
                return

            ents, rels = extract_kg_from_case(
                engine.ai_assistant,
                case_id=c.id,
                title=c.title,
                domain=c.domain,
                text=text,
            )

            try:
                self._kg_store.upsert_entities(ents)
            except Exception:
                pass

            try:
                rel_rows: List[Dict[str, Any]] = []
                for r in rels:
                    rr = dict(r)
                    rr["case_id"] = c.id
                    rr["evidence_id"] = f"ev_{r['id']}_{c.id}"[:64]
                    rel_rows.append(rr)
                self._kg_store.upsert_relations_with_evidence(rel_rows)
            except Exception:
                pass

            try:
                engine.db.upsert_kg_case_state(case_id=c.id, text_sha1=sha1)
            except Exception:
                pass

            try:
                if self._kg_cache is not None:
                    self._kg_cache.invalidate_prefix("kg:subgraph:")
            except Exception:
                pass

            try:
                if self._hot_index is not None:
                    self._hot_index.refresh(limit=50)
            except Exception:
                pass

            events.emit("kg.extracted", {"case_id": c.id})
        except Exception:
            return
