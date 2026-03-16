from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..ai.decision_assistant import AIDecisionAssistant
from ..models.case import Case
from ..storage.database import Database
from ..utils.config import Config
from ..knowledge.hot_index import HotIndex
from .chunker import chunk_text
from .embedder import EmbeddingClient
from .qdrant_store import QdrantVectorStore


@dataclass
class GraphRAGResult:
    cases: List[Case]
    reasoning: str
    recommendations: List[str]


class GraphRAGService:
    def __init__(
        self,
        *,
        config: Config,
        db: Database,
        ai: AIDecisionAssistant,
        hot_index: HotIndex,
        kg_store: Any,
    ):
        self._config = config
        self._db = db
        self._ai = ai
        self._hot_index = hot_index
        self._kg_store = kg_store

        self._enabled = bool(config.get("graphrag.enabled", True))

        qcfg = config.get("graphrag.qdrant", {}) or {}
        self._qdrant_url = str(qcfg.get("url") or "").strip() or "http://127.0.0.1:6333"
        self._collection = str(qcfg.get("collection") or "vw_case_chunks")
        self._vector_size_cfg = int(qcfg.get("vector_size") or 0) or None

        ecfg = config.get("graphrag.embedding", {}) or {}
        self._embedder = EmbeddingClient(
            provider=str(ecfg.get("provider") or "ollama"),
            model=str(ecfg.get("model") or "nomic-embed-text"),
            api_base=str(ecfg.get("api_base") or "") or None,
            api_key=str(ecfg.get("api_key") or "") or None,
        )

        ccfg = config.get("graphrag.chunking", {}) or {}
        self._max_chars = int(ccfg.get("max_chars") or 1400)
        self._overlap_chars = int(ccfg.get("overlap_chars") or 200)

    def _store(self) -> QdrantVectorStore:
        return QdrantVectorStore(url=self._qdrant_url, collection=self._collection, vector_size=self._vector_size_cfg)

    def index_cases(self, *, case_ids: Optional[List[str]] = None, limit: int = 0) -> Dict[str, Any]:
        if not self._enabled:
            return {"status": "disabled"}

        store = self._store()

        cases = self._db.list_cases()
        if case_ids:
            wanted = set(case_ids)
            cases = [c for c in cases if c.id in wanted]
        if limit:
            cases = cases[: max(0, int(limit))]

        points: List[Dict[str, Any]] = []
        total_chunks = 0
        vector_size: Optional[int] = None

        for c in cases:
            full = "\n".join(
                [
                    c.title or "",
                    c.description or "",
                    c.decision_node or "",
                    c.action_taken or "",
                    c.outcome_result or "",
                    c.lesson_core or "",
                ]
            ).strip()
            if not full:
                continue

            chunks = chunk_text(text=full, max_chars=self._max_chars, overlap_chars=self._overlap_chars)
            for ch in chunks:
                text = ch.text
                v = self._embedder.embed(text)
                if not v:
                    continue
                if vector_size is None:
                    vector_size = len(v)
                    store.ensure_collection(vector_size=vector_size)
                elif len(v) != vector_size:
                    return {
                        "status": "error",
                        "message": f"embedding dim mismatch: expected {vector_size}, got {len(v)}",
                    }

                pid = f"{c.id}::{ch.chunk_id}"
                points.append(
                    {
                        "id": pid,
                        "vector": v,
                        "payload": {
                            "case_id": c.id,
                            "title": c.title,
                            "domain": c.domain,
                            "chunk_id": ch.chunk_id,
                            "text": text[:2000],
                        },
                    }
                )
                total_chunks += 1

        if points:
            store.upsert(points=points)

        return {
            "status": "ok",
            "cases_indexed": len(cases),
            "chunks_indexed": total_chunks,
            "vector_size": vector_size or self._vector_size_cfg,
        }

    def query(self, *, text: str, top_k: int = 20) -> GraphRAGResult:
        if not self._enabled:
            return GraphRAGResult(cases=[], reasoning="GraphRAG disabled", recommendations=[])

        q = (text or "").strip()
        if not q:
            return GraphRAGResult(cases=[], reasoning="", recommendations=[])

        store = self._store()
        qv = self._embedder.embed(q)
        if not qv:
            return GraphRAGResult(cases=[], reasoning="Embedding failed", recommendations=[])

        hits = store.search(query_vector=qv, top_k=int(top_k))
        # group by case
        case_scores: Dict[str, float] = {}
        case_snips: Dict[str, List[str]] = {}
        for h in hits:
            cid = str(h.payload.get("case_id") or "")
            if not cid:
                continue
            case_scores[cid] = max(case_scores.get(cid, 0.0), float(h.score or 0.0))
            txt = str(h.payload.get("text") or "")
            if txt:
                case_snips.setdefault(cid, []).append(txt[:400])

        ranked = sorted(case_scores.items(), key=lambda x: x[1], reverse=True)
        case_ids = [cid for cid, _ in ranked[:5]]
        cases: List[Case] = []
        for cid in case_ids:
            try:
                cases.append(self._db.get_case(cid))
            except Exception:
                continue

        # try seed entities from hot index simple match (best-effort)
        seeds: List[str] = []
        try:
            seeds = self._hot_index.match_ids(query=q, max_hits=6)
        except Exception:
            seeds = []

        kg_ctx: Dict[str, Any] = {}
        if seeds:
            try:
                sub = self._kg_store.query_subgraph(seed_entity_id=seeds[0], depth=2, max_entities=160, max_relations=260)
                kg_ctx = {"seed": seeds[0], "nodes": sub.nodes[:120], "edges": sub.edges[:200]}
            except Exception:
                kg_ctx = {}

        evidence: List[Dict[str, Any]] = []
        for cid in case_ids:
            for s in (case_snips.get(cid) or [])[:2]:
                evidence.append({"case_id": cid, "snippet": s})

        prompt = self._build_prompt(query=q, cases=cases, evidence=evidence, kg_ctx=kg_ctx)
        raw = self._ai._call_ai(prompt) or ""

        reasoning, recs = _parse_3a(raw)
        return GraphRAGResult(cases=cases, reasoning=reasoning, recommendations=recs)

    def _build_prompt(self, *, query: str, cases: List[Case], evidence: List[Dict[str, Any]], kg_ctx: Dict[str, Any]) -> str:
        cases_text = "\n".join(
            [
                f"- case_id={c.id} title={c.title} domain={c.domain} lesson={((c.lesson_core or '')[:180]).strip()}"
                for c in cases
            ]
        )
        ev_text = "\n".join([f"- case_id={e['case_id']} snippet={e['snippet']}" for e in evidence])
        kg_text = json.dumps(kg_ctx, ensure_ascii=False)[:2500] if kg_ctx else "{}"

        return f"""你是一个个人历史教训复用系统的 GraphRAG 分析器。请根据向量召回证据 + 图谱上下文给出答案。

用户问题：
{query}

召回案例（仅供参考）：
{cases_text}

证据片段（必须引用 case_id）：
{ev_text}

图谱上下文（可能为空，JSON）：
{kg_text}

请输出：
1) 结论：一句话总结
2) 关键证据：列出 3-6 条，每条必须包含 case_id
3) 风险类型/触发事件：列出可能的 RiskType / Event（如果缺少就写“未知”）
4) 行动建议：3-6 条可执行建议

输出格式：
CONCLUSION:
...

EVIDENCE:
- case_id=... ...

RISK_TYPES:
- ...

TRIGGERS:
- ...

ACTIONS:
- ...
"""


def _parse_3a(raw: str) -> Tuple[str, List[str]]:
    s = (raw or "").strip()
    if not s:
        return "", []

    # Simple parsing: keep entire text as reasoning, actions as recommendations if present
    reasoning = s
    recs: List[str] = []
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    in_actions = False
    for ln in lines:
        up = ln.upper()
        if up.startswith("ACTIONS"):
            in_actions = True
            continue
        if in_actions and ln.startswith("-"):
            recs.append(ln.lstrip("- ").strip())
    if not recs:
        # fallback: first few bullet lines anywhere
        for ln in lines:
            if ln.startswith("-"):
                recs.append(ln.lstrip("- ").strip())
            if len(recs) >= 5:
                break

    return reasoning, recs[:6]
