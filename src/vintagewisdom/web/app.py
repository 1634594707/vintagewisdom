from datetime import datetime
import hashlib
import io
import json
import re
import uuid
import threading
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
import tempfile

import yaml

from fastapi import Body, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    text: str
    mode: str | None = None


class QueryResponse(BaseModel):
    matches: int
    cases: List[Dict[str, Any]]
    reasoning: str
    recommendations: List[str]


class DecisionLogRequest(BaseModel):
    id: Optional[str] = None
    query: str
    context: Dict[str, Any] = Field(default_factory=dict)
    recommended_cases: List[str] = Field(default_factory=list)
    choice: Optional[str] = None
    predict: Optional[str] = None


class EvaluateDecisionRequest(BaseModel):
    outcome: str


class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    suggestions: List[Dict[str, Any]]


class KGRebuildResponse(BaseModel):
    status: str
    cases_processed: int
    entities_upserted: int
    relations_upserted: int
    evidence_upserted: int


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _normalize_header(name: str) -> str:
    return "".join(ch for ch in name.strip().lower().replace("-", "_") if ch.isalnum() or ch == "_")


def _normalize_ingest_value(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float, bool)):
        return str(v)
    if isinstance(v, (dict, list)):
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)
    return str(v)


def _auto_column_map(headers: list[str]) -> Dict[str, str]:
    normalized = {_normalize_header(h): h for h in headers}
    # 同时保留原始字段名用于直接匹配中文
    original_headers = {h: h for h in headers}

    def pick(*candidates: str) -> str | None:
        for c in candidates:
            if c in normalized:
                return normalized[c]
            # 直接匹配原始字段名（支持中文）
            if c in original_headers:
                return original_headers[c]
        return None

    mapping: Dict[str, str] = {}
    id_col = pick("id", "case_id", "caseid", "案例名称", "案例id", "案例ID")
    if id_col:
        mapping["id"] = id_col

    # domain should be a stable enum like HIS/FIN/CAR/TEC (or subcodes).
    # Do NOT map free-text risk_type into domain; keep it for description/decision_node.
    domain_col = pick("domain", "领域")
    if domain_col:
        mapping["domain"] = domain_col

    title_col = pick("title", "name", "标题", "股灾名称", "案例名称", "事件名称")
    if title_col:
        mapping["title"] = title_col

    desc_col = pick(
        "description",
        "desc",
        "描述",
        "触发事件",
        "根本原因",
        "历史教训",
        "核心影响与结果",
        "核心损失及结果",
        "核心影响",
    )
    if desc_col:
        mapping["description"] = desc_col

    decision_node_col = pick("decision_node", "decision", "决策节点", "风险类型")
    if decision_node_col:
        mapping["decision_node"] = decision_node_col

    action_col = pick("action_taken", "action", "采取行动", "应对策略")
    if action_col:
        mapping["action_taken"] = action_col

    outcome_col = pick(
        "outcome_result",
        "outcome",
        "结果",
        "核心指数及跌幅",
        "核心损失及结果",
        "核心影响与结果",
        "核心影响",
    )
    if outcome_col:
        mapping["outcome_result"] = outcome_col

    timeline_col = pick("outcome_timeline", "timeline", "历时", "时间线", "发生时间")
    if timeline_col:
        mapping["outcome_timeline"] = timeline_col

    lesson_col = pick("lesson_core", "lesson", "教训", "核心教训", "历史教训")
    if lesson_col:
        mapping["lesson_core"] = lesson_col

    confidence_col = pick("confidence", "置信度", "预警信号")
    if confidence_col:
        mapping["confidence"] = confidence_col

    return mapping


def _build_case_from_row(
    row: Dict[str, str],
    *,
    column_map: Dict[str, str],
    default_domain: str,
    tags: Optional[List[str]] = None,
    auto_classify: bool = False,
) -> Dict[str, Any]:
    from ..knowledge.domains import auto_classify_domain
    
    def get(field: str) -> str:
        col = column_map.get(field)
        if col and col in row:
            return (row.get(col) or "").strip()
        if field == "domain":
            return (default_domain or "").strip()
        return ""

    case_id = get("id")
    domain = get("domain")
    title = get("title")

    # 如果没有domain且启用自动分类，则自动分类
    if not domain and auto_classify:
        row_text = " ".join(str(v) for v in row.values() if v)
        classify_results = auto_classify_domain(row_text)
        if classify_results:
            domain = classify_results[0]["domain"]
    
    # 如果仍然没有domain，使用默认值或报错
    if not domain:
        if default_domain:
            domain = default_domain
        else:
            domain = "GENERAL"  # 使用通用领域作为默认值
    
    if not title:
        raise ValueError(f"Missing required field: title (case id: {case_id})")

    if not case_id:
        raw = "\n".join(f"{k}:{(v or '').strip()}" for k, v in row.items() if (v or '').strip())
        case_id = f"case_{_sha256_bytes(raw.encode('utf-8'))[:16]}"

    mapped_cols = set(v for v in column_map.values() if v)
    desc = get("description")
    if not desc:
        parts: list[str] = []
        for k, v in row.items():
            if k in mapped_cols:
                continue
            vv = (v or "").strip()
            if not vv:
                continue
            parts.append(f"{k}: {vv}")
        desc = "\n".join(parts).strip()

    now = datetime.utcnow()
    return {
        "id": case_id,
        "domain": domain,
        "title": title,
        "description": desc or None,
        "decision_node": get("decision_node") or None,
        "action_taken": get("action_taken") or None,
        "outcome_result": get("outcome_result") or None,
        "outcome_timeline": get("outcome_timeline") or None,
        "lesson_core": get("lesson_core") or None,
        "confidence": get("confidence") or None,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }


def _extract_text_from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing PDF dependency. Install with: pip install -e '.[ingest]'") from e

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def _extract_text_from_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing DOCX dependency. Install with: pip install -e '.[ingest]'") from e

    d = docx.Document(str(path))
    parts: list[str] = []
    for para in d.paragraphs:
        t = (para.text or "").strip()
        if t:
            parts.append(t)
    return "\n".join(parts).strip()


def _extract_document_text(path: Path, doc_type: str) -> str:
    resolved = doc_type
    if resolved == "auto":
        resolved = path.suffix.lower().lstrip(".")

    if resolved == "pdf":
        return _extract_text_from_pdf(path)
    if resolved == "docx":
        return _extract_text_from_docx(path)

    raise RuntimeError(f"Unsupported document type: {doc_type}")


def _extract_markdown_note(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").replace("\r\n", "\n")
    meta: Dict[str, Any] = {}
    body = text

    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = text[4:end]
            body = text[end + len("\n---\n") :]
            try:
                parsed = yaml.safe_load(fm)
                if isinstance(parsed, dict):
                    meta = parsed
            except Exception:
                meta = {}

    title = str(meta.get("title") or meta.get("name") or "").strip()
    if not title:
        m = re.search(r"^\s*#\s+(.+?)\s*$", body, flags=re.MULTILINE)
        if m:
            title = m.group(1).strip()

    return {"meta": meta, "title": title, "body": body.strip()}


def _coerce_json_cases_payload(payload: Any) -> List[Dict[str, Any]]:
    """Coerce various JSON payload shapes into a list[dict]."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("cases", "items", "data", "rows"):
            v = payload.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        # single object
        return [payload]
    return []


def create_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import RedirectResponse

    from ..core.app import VintageWisdomApp
    from ..models.decision import DecisionLog
    from ..knowledge.domains import auto_classify_domain, find_similar_cases

    app = FastAPI(title="VintageWisdom API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    vw_app = VintageWisdomApp()
    vw_app.initialize()
    engine = vw_app.engine
    from ..core.events import events

    from ..knowledge.kg_store import get_kg_cache, get_kg_store
    from ..knowledge.hot_index import HotIndex
    from ..knowledge.kg_store import KGStore

    kg_store = get_kg_store(engine.config, engine.db)
    kg_cache, kg_cache_ttl = get_kg_cache(engine.config)
    hot_index = HotIndex(kg_store=kg_store)
    try:
        hot_index.refresh(limit=50)
    except Exception:
        pass

    # Web layer only cares about keeping caches fresh; extraction happens in plugins.
    def _on_kg_extracted(ev) -> None:
        try:
            kg_cache.invalidate_prefix("kg:subgraph:")
        except Exception:
            pass
        try:
            hot_index.refresh(limit=50)
        except Exception:
            pass

    try:
        events.on("kg.extracted", _on_kg_extracted)
    except Exception:
        pass

    # Background refresh to keep hot index warm without impacting request latency
    def _start_hot_index_refresher() -> None:
        try:
            seconds = int(engine.config.get("kg.hot_index.refresh_seconds", 60) or 60)
        except Exception:
            seconds = 60
        seconds = max(10, min(seconds, 3600))

        def worker() -> None:
            while True:
                try:
                    time.sleep(seconds)
                    hot_index.refresh(limit=50)
                except Exception:
                    # keep thread alive even if neo4j is temporarily unavailable
                    continue

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    _start_hot_index_refresher()

    # KG extraction moved to kg.extract plugin.

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/stats")
    def stats() -> Dict[str, int]:
        return {
            "cases": engine.db.count_cases(),
            "decision_logs": engine.db.count_decision_logs(),
            "evaluated_decision_logs": engine.db.count_evaluated_decision_logs(),
        }

    @app.get("/cases")
    def list_cases() -> List[Dict[str, Any]]:
        return [c.model_dump() for c in engine.db.list_cases()]

    @app.get("/cases/{case_id}")
    def get_case(case_id: str) -> Dict[str, Any]:
        try:
            case = engine.db.get_case(case_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="case not found")
        return case.model_dump()

    @app.get("/cases/{case_id}/similar")
    def get_similar_cases(case_id: str, threshold: float = 0.3) -> Dict[str, Any]:
        """获取与指定案例相似的案例"""
        try:
            target_case = engine.db.get_case(case_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="case not found")
        
        all_cases = [c.model_dump() for c in engine.db.list_cases()]
        target_dict = target_case.model_dump()
        
        similar = find_similar_cases(all_cases, target_dict, threshold)
        return {
            "case_id": case_id,
            "similar_cases": similar
        }

    @app.post("/classify", response_model=ClassifyResponse)
    def classify_text(req: ClassifyRequest) -> ClassifyResponse:
        """AI自动分类文本"""
        suggestions = auto_classify_domain(req.text)
        return ClassifyResponse(suggestions=suggestions)

    @app.get("/graph")
    def graph(
        view: str = "case",
        q: str = "",
        seed_entity_id: str = "",
        relation_type: str = "",
        depth: int = 2,
        max_entities: int = 300,
        max_relations: int = 600,
        use_ai_clustering: bool = False,
        similarity_threshold: float = 0.4,
        max_cases_for_similarity: int = 200,
        max_similar_edges: int = 60
    ) -> Dict[str, Any]:
        """
        获取知识图谱数据，包含 AI 聚类和案例相似关系
        
        Args:
            use_ai_clustering: 是否使用 AI 进行案例聚类
            similarity_threshold: 案例相似度阈值
        """
        from ..knowledge.domains import calculate_similarity, get_main_domain
        
        # KG 视图：返回 Entity/Relation 图谱（支持搜索与邻域展开）
        if view.lower() in {"kg", "entity", "entities"}:
            seed = (seed_entity_id or "").strip()
            query = (q or "").strip()
            rel_type = (relation_type or "").strip()
            dd = max(1, min(int(depth or 1), 3))
            cache_key = f"kg:subgraph:seed={seed}:q={query}:rt={rel_type}:d={dd}:me={int(max_entities)}:mr={int(max_relations)}"

            cached = kg_cache.get(cache_key)
            if cached:
                return cached

            sub = kg_store.query_subgraph(
                q=query,
                seed_entity_id=seed,
                relation_type=rel_type,
                depth=dd,
                max_entities=int(max_entities),
                max_relations=int(max_relations),
            )
            resp = {"nodes": sub.nodes, "edges": sub.edges, "stats": sub.stats}

            # unify strength for frontend rendering
            try:
                for e in resp.get("edges", []) or []:
                    if isinstance(e, dict) and "strength" not in e:
                        c = e.get("confidence")
                        if isinstance(c, (int, float)):
                            e["strength"] = float(c)
            except Exception:
                pass

            kg_cache.set(cache_key, resp, ttl_seconds=kg_cache_ttl)
            return resp

        # Case graph view: cache to avoid recomputing similarity/clustering repeatedly
        case_count = 0
        try:
            case_count = int(engine.db.count_cases() or 0)
        except Exception:
            case_count = 0

        cache_key = (
            f"case:graph:cases={case_count}:ai={int(bool(use_ai_clustering))}:"
            f"st={similarity_threshold}:mcs={int(max_cases_for_similarity)}:mse={int(max_similar_edges)}"
        )
        cached = kg_cache.get(cache_key)
        if cached:
            return cached

        cases = engine.db.list_cases()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        
        # 转换为字典格式便于处理
        case_dicts = [c.model_dump() for c in cases]

        # 1. 创建 Domain 节点
        domain_ids: Dict[str, str] = {}
        domain_case_map: Dict[str, List[str]] = {}
        
        for c in cases:
            dom = (c.domain or "").strip() or "unknown"
            if dom not in domain_ids:
                dom_id = f"domain:{dom}"
                domain_ids[dom] = dom_id
                nodes.append(
                    {
                        "id": dom_id,
                        "type": "domain",
                        "label": dom,
                        "domain": dom,
                    }
                )
            
            # 记录 domain -> case 映射
            if dom not in domain_case_map:
                domain_case_map[dom] = []
            domain_case_map[dom].append(c.id)

        # 2. 创建 Case 节点
        case_id_to_node: Dict[str, Dict] = {}
        for c in cases:
            dom = (c.domain or "").strip() or "unknown"
            case_node_id = f"case:{c.id}"
            case_node = {
                "id": case_node_id,
                "type": "case",
                "label": c.title,
                "case_id": c.id,
                "domain": dom,
                # large text fields are lazy-loaded by /cases/{id}
            }
            nodes.append(case_node)
            case_id_to_node[c.id] = case_node
            
            # Domain -> Case 边
            edges.append(
                {
                    "id": f"e:{domain_ids[dom]}->{case_node_id}",
                    "source": domain_ids[dom],
                    "target": case_node_id,
                    "type": "has_case",
                    "edge_type": "domain_case",
                }
            )
        
        # 3. 计算案例间相似度并创建相似边（注意：大数据量时避免 O(n^2)）
        similar_edges: List[Dict[str, Any]] = []
        case_list = list(cases)

        # 限制用于相似度计算的案例数，避免数据量大时接口卡死。
        # 策略：优先取最新 updated_at 的一批（通常更有用），再做两两比较。
        if max_cases_for_similarity > 0 and len(case_list) > max_cases_for_similarity:
            try:
                case_list.sort(key=lambda c: (c.updated_at or c.created_at), reverse=True)
            except Exception:
                pass
            case_list = case_list[:max_cases_for_similarity]

        # 兜底：如果 max_similar_edges 非法，设一个合理值
        if max_similar_edges <= 0:
            max_similar_edges = 0

        for i in range(len(case_list)):
            for j in range(i + 1, len(case_list)):
                if max_similar_edges and len(similar_edges) >= max_similar_edges * 5:
                    # 先粗略截断，后续排序再取 top-k
                    break
                case1 = case_list[i]
                case2 = case_list[j]

                similarity, reasons = calculate_similarity(case1.model_dump(), case2.model_dump())

                if similarity >= similarity_threshold:
                    similar_edges.append(
                        {
                            "id": f"similar:{case1.id}:{case2.id}",
                            "source": f"case:{case1.id}",
                            "target": f"case:{case2.id}",
                            "type": "similar",
                            "edge_type": "case_similar",
                            "similarity": similarity,
                            "reasons": reasons,
                        }
                    )

        # 按相似度排序，限制边数量避免图谱过于复杂
        similar_edges.sort(key=lambda x: x["similarity"], reverse=True)
        if max_similar_edges:
            similar_edges = similar_edges[:max_similar_edges]
        
        edges.extend(similar_edges)

        # unify strength for frontend rendering
        try:
            for e in edges:
                if not isinstance(e, dict):
                    continue
                if "strength" in e:
                    continue
                if e.get("edge_type") == "case_similar":
                    s = e.get("similarity")
                    if isinstance(s, (int, float)):
                        e["strength"] = float(s)
                else:
                    c = e.get("confidence")
                    if isinstance(c, (int, float)):
                        e["strength"] = float(c)
        except Exception:
            pass
        
        # 4. 使用 AI 进行聚类（如果启用且案例数量足够）
        clusters = []
        if use_ai_clustering and len(cases) >= 3:
            try:
                from ..ai.case_clustering import get_clustering_engine
                clustering_engine = get_clustering_engine(
                    model=engine.config.get("ai.model", "deepseek-r1:7b")
                )
                
                if clustering_engine:
                    clusters = clustering_engine.cluster_cases(case_dicts, min_cluster_size=2)
                    
                    # 为每个聚类创建聚类节点
                    for cluster in clusters:
                        cluster_id = f"cluster:{cluster['cluster_id']}"
                        nodes.append({
                            "id": cluster_id,
                            "type": "cluster",
                            "label": cluster['cluster_name'],
                            "cluster_theme": cluster['theme'],
                        })
                        
                        # 创建聚类 -> case 的边
                        for case_id in cluster['cases']:
                            if case_id in case_id_to_node:
                                edges.append({
                                    "id": f"e:{cluster_id}->{case_id}",
                                    "source": cluster_id,
                                    "target": f"case:{case_id}",
                                    "type": "has_case",
                                    "edge_type": "cluster_case",
                                })
            except Exception as e:
                print(f"AI clustering failed: {e}")
        
        resp = {
            "nodes": nodes, 
            "edges": edges,
            "clusters": clusters,
            "stats": {
                "domain_count": len(domain_ids),
                "case_count": len(cases),
                "similar_edge_count": len(similar_edges),
                "cluster_count": len(clusters),
                "similarity_cases_used": len(case_list),
            }
        }

        kg_cache.set(cache_key, resp, ttl_seconds=kg_cache_ttl)
        return resp

    @app.get("/kg/node/{entity_id}")
    def kg_node_details(entity_id: str) -> Dict[str, Any]:
        """按需加载 KG 节点详情（包含可能较大的 attributes）。"""
        eid = (entity_id or "").strip()
        if not eid:
            raise HTTPException(status_code=400, detail="entity_id required")

        # SQLite store: read from local DB
        if kg_store.__class__.__name__ == "SqliteKGStore":
            rows = engine.db.get_entities_by_ids([eid])
            if not rows:
                raise HTTPException(status_code=404, detail="entity not found")
            e = rows[0]
            return {
                "id": e.get("id"),
                "type": e.get("type") or "entity",
                "label": e.get("name") or e.get("id"),
                "attributes": e.get("attributes") or {},
            }

        # Neo4j store: fetch only required fields; attributes stored as JSON string
        if kg_store.__class__.__name__ == "Neo4jKGStore":
            try:
                with kg_store._driver.session(database=kg_store._database) as s:  # type: ignore[attr-defined]
                    row = s.run(
                        """
                        MATCH (e {id: $id})
                        WHERE (e:Crash OR e:RiskType OR e:Event OR e:Entity)
                        RETURN e.id AS id, e.name AS name, e.type AS type, e.attributes AS attributes
                        """,
                        id=eid,
                    ).single()
            except Exception:
                row = None

            if not row:
                raise HTTPException(status_code=404, detail="entity not found")

            attrs_raw = row.get("attributes")
            attrs: Dict[str, Any] = {}
            if isinstance(attrs_raw, str) and attrs_raw:
                try:
                    attrs = json.loads(attrs_raw)
                except Exception:
                    attrs = {"raw": attrs_raw}

            return {
                "id": row.get("id"),
                "type": row.get("type") or "entity",
                "label": row.get("name") or row.get("id"),
                "attributes": attrs,
            }

        raise HTTPException(status_code=500, detail="unsupported kg store")

    @app.get("/kg/hot")
    def kg_hot(limit: int = 50) -> Dict[str, Any]:
        """高频查询：热门风险类型/事件等，优先走 Python 内存。"""
        snap = hot_index.snapshot()
        try:
            lim = max(1, min(int(limit or 50), 200))
        except Exception:
            lim = 50
        if isinstance(snap.get("risk_types"), list):
            snap["risk_types"] = snap["risk_types"][:lim]
        if isinstance(snap.get("events"), list):
            snap["events"] = snap["events"][:lim]
        return snap

    @app.get("/kg/lookup")
    def kg_lookup(kind: str = "", name: str = "") -> Dict[str, Any]:
        """高频查询：通过名称查找实体 id（不查 Neo4j）。"""
        eid = hot_index.lookup(kind=kind, name=name)
        return {"id": eid, "kind": kind, "name": name}

    @app.post("/kg/rebuild", response_model=KGRebuildResponse)
    def kg_rebuild(limit_cases: int = Body(50), force: bool = Body(False)) -> KGRebuildResponse:
        from ..knowledge.kg_extractor import extract_kg_from_case

        engine.db.initialize()

        cases = engine.db.list_cases()
        cases = cases[: max(0, int(limit_cases))] if limit_cases else cases

        entities_upserted = 0
        relations_upserted = 0
        evidence_upserted = 0

        for c in cases:
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
                continue

            ents, rels = extract_kg_from_case(
                engine.ai_assistant,
                case_id=c.id,
                title=c.title,
                domain=c.domain,
                text=text,
            )

            for e in ents:
                engine.db.upsert_entity(
                    entity_id=e["id"],
                    name=e["name"],
                    entity_type=e["type"],
                    attributes=e.get("attributes") or {},
                    updated_at=e.get("updated_at"),
                )
                entities_upserted += 1

            for r in rels:
                engine.db.upsert_relation(
                    relation_id=r["id"],
                    source_entity_id=r["source"],
                    target_entity_id=r["target"],
                    relation_type=r["relation_type"],
                    confidence=float(r.get("confidence") or 0.5),
                    attributes=r.get("attributes") or {},
                    updated_at=r.get("updated_at"),
                )
                relations_upserted += 1

                ev_id = f"ev_{r['id']}_{c.id}"[:64]
                engine.db.add_relation_evidence(
                    evidence_id=ev_id,
                    relation_id=r["id"],
                    case_id=c.id,
                    quote=str(r.get("quote") or "")[:2000],
                    start_offset=None,
                    end_offset=None,
                )
                evidence_upserted += 1

        kg_cache.invalidate_prefix("kg:subgraph:")
        try:
            hot_index.refresh(limit=50)
        except Exception:
            pass

        return KGRebuildResponse(
            status="ok",
            cases_processed=len(cases),
            entities_upserted=entities_upserted,
            relations_upserted=relations_upserted,
            evidence_upserted=evidence_upserted,
        )

    @app.post("/ingest/csv")
    async def ingest_csv(
        file: UploadFile = File(...),
        default_domain: str = Form(""),
        on_conflict: str = Form("skip"),
        auto_classify: str = Form("false"),
        domains: str = Form(""),
        tags: str = Form(""),
    ) -> Dict[str, Any]:
        raw = await file.read()
        sha = _sha256_bytes(raw)
        try:
            events.emit("ingest.started", {"type": "csv", "sha256": sha, "filename": file.filename or ""})
        except Exception:
            pass
        existing = engine.db.get_file_ingest_by_sha256(sha)
        if existing and existing.get("status") == "success":
            return {
                "status": "skipped",
                "sha256": sha,
                "imported": int(existing.get("imported_count") or 0),
                "skipped": int(existing.get("skipped_count") or 0),
                "failed": int(existing.get("failed_count") or 0),
                "message": "Already ingested",
            }

        ingest_id = f"csv_{sha}"
        engine.db.upsert_file_ingest(
            ingest_id=ingest_id,
            source_type="csv_upload",
            source_path=file.filename or "",
            source_sha256=sha,
            source_mtime=None,
            status="running",
            message=None,
        )

        # 解析domains和tags
        selected_domains = json.loads(domains) if domains else []
        selected_tags = json.loads(tags) if tags else []
        enable_auto_classify = auto_classify.lower() == "true"
        
        # 如果用户选择了领域，使用第一个作为默认领域
        if selected_domains and not default_domain:
            default_domain = selected_domains[0]

        imported = 0
        skipped = 0
        failed = 0
        case_ids: List[str] = []
        suggested_domains: List[str] = []
        
        try:
            text = raw.decode("utf-8-sig", errors="replace")
            reader = io.StringIO(text)
            csv_reader = __import__("csv").DictReader(reader)
            if csv_reader.fieldnames is None:
                raise RuntimeError("CSV has no header row")
            column_map = _auto_column_map(list(csv_reader.fieldnames))

            for i, row in enumerate(csv_reader, start=2):
                try:
                    # 如果启用自动分类且没有指定domain
                    row_domain = row.get(column_map.get("domain", ""), "")
                    if enable_auto_classify and not row_domain and not default_domain:
                        # 从行内容自动分类
                        row_text = " ".join(str(v) for v in row.values() if v)
                        classify_results = auto_classify_domain(row_text)
                        if classify_results:
                            row[column_map.get("domain", "domain")] = classify_results[0]["domain"]
                            if classify_results[0]["domain"] not in suggested_domains:
                                suggested_domains.append(classify_results[0]["domain"])
                    
                    data = _build_case_from_row(
                        row, 
                        column_map=column_map, 
                        default_domain=default_domain,
                        tags=selected_tags,
                        auto_classify=enable_auto_classify
                    )
                    case_id = str(data["id"])
                    if on_conflict == "skip" and engine.db.case_exists(case_id):
                        skipped += 1
                        continue
                    from ..models.case import Case

                    engine.add_case(Case(**data))
                    imported += 1
                    case_ids.append(case_id)
                except Exception as e:
                    import traceback
                    print(f"Failed to import row {idx}: {e}")
                    print(traceback.format_exc())
                    failed += 1
                    continue

            status = "success" if failed == 0 else "partial"
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="csv_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status=status,
                imported_count=imported,
                skipped_count=skipped,
                failed_count=failed,
                message=None,
            )

            # KG extraction handled by plugin via events
            try:
                events.emit(
                    "ingest.completed",
                    {"type": "csv", "sha256": sha, "case_ids": case_ids, "status": status},
                )
            except Exception:
                pass
            return {
                "status": status,
                "sha256": sha,
                "imported": imported,
                "skipped": skipped,
                "failed": failed,
                "case_ids": case_ids,
                "auto_classified": enable_auto_classify and len(suggested_domains) > 0,
                "suggested_domains": suggested_domains if enable_auto_classify else None,
            }
        except Exception as e:
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="csv_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status="failed",
                imported_count=imported,
                skipped_count=skipped,
                failed_count=max(1, failed),
                message=str(e),
            )
            try:
                events.emit("ingest.failed", {"type": "csv", "sha256": sha, "error": str(e)})
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/ingest/markdown")
    async def ingest_markdown(
        file: UploadFile = File(...),
        case_id: str = Form(""),
        domain: str = Form(""),
        title: str = Form(""),
        auto_classify: str = Form("false"),
        domains: str = Form(""),
        tags: str = Form(""),
    ) -> Dict[str, Any]:
        raw = await file.read()
        sha = _sha256_bytes(raw)
        try:
            events.emit("ingest.started", {"type": "markdown", "sha256": sha, "filename": file.filename or ""})
        except Exception:
            pass
        existing = engine.db.get_file_ingest_by_sha256(sha)
        if existing and existing.get("status") == "success":
            return {"status": "skipped", "sha256": sha, "message": "Already ingested"}

        ingest_id = f"md_{sha}"
        engine.db.upsert_file_ingest(
            ingest_id=ingest_id,
            source_type="markdown_upload",
            source_path=file.filename or "",
            source_sha256=sha,
            source_mtime=None,
            status="running",
            message=None,
        )

        selected_domains = json.loads(domains) if domains else []
        selected_tags = json.loads(tags) if tags else []
        enable_auto_classify = auto_classify.lower() == "true"

        try:
            text = raw.decode("utf-8", errors="replace")
            note = _extract_markdown_note(text)
            meta = note.get("meta") if isinstance(note.get("meta"), dict) else {}
            body = str(note.get("body") or "")

            now = datetime.utcnow()
            resolved_id = (case_id or "").strip() or f"case_{sha[:16]}"

            suggested_domains: List[str] = []
            if enable_auto_classify and not domain and not selected_domains:
                classify_results = auto_classify_domain(body)
                if classify_results:
                    suggested_domains = [r["domain"] for r in classify_results[:3]]
                    selected_domains = [classify_results[0]["domain"]]

            resolved_domain = (
                (domain or "").strip()
                or (str(meta.get("domain") or "").strip())
                or (selected_domains[0] if selected_domains else "general")
            )
            resolved_title = (
                (title or "").strip()
                or str(note.get("title") or "").strip()
                or str(meta.get("title") or "").strip()
                or (Path(file.filename or "note").stem)
            )

            if engine.db.case_exists(resolved_id):
                engine.db.upsert_file_ingest(
                    ingest_id=ingest_id,
                    source_type="markdown_upload",
                    source_path=file.filename or "",
                    source_sha256=sha,
                    source_mtime=None,
                    status="skipped",
                    imported_count=0,
                    skipped_count=1,
                    failed_count=0,
                    message=f"Case id already exists: {resolved_id}",
                )
                return {"status": "skipped", "sha256": sha, "case_id": resolved_id, "message": "Case id already exists"}

            from ..models.case import Case

            engine.add_case(
                Case(
                    id=resolved_id,
                    domain=resolved_domain,
                    title=resolved_title[:300],
                    description=(body[:8000] if body else "") or None,
                    tags=selected_tags,
                    created_at=now,
                    updated_at=now,
                )
            )

            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="markdown_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status="success",
                imported_count=1,
                skipped_count=0,
                failed_count=0,
                message=None,
            )
            try:
                events.emit(
                    "ingest.completed",
                    {"type": "markdown", "sha256": sha, "case_ids": [resolved_id], "status": "success"},
                )
            except Exception:
                pass
            return {
                "status": "success",
                "sha256": sha,
                "case_id": resolved_id,
                "auto_classified": enable_auto_classify and len(suggested_domains) > 0,
                "suggested_domains": suggested_domains if enable_auto_classify else None,
            }
        except Exception as e:
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="markdown_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status="failed",
                imported_count=0,
                skipped_count=0,
                failed_count=1,
                message=str(e),
            )
            try:
                events.emit("ingest.failed", {"type": "markdown", "sha256": sha, "error": str(e)})
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/ingest/document")
    async def ingest_document(
        file: UploadFile = File(...),
        doc_type: str = Form("auto"),
        case_id: str = Form(""),
        domain: str = Form(""),
        title: str = Form(""),
        auto_classify: str = Form("false"),
        domains: str = Form(""),
        tags: str = Form(""),
    ) -> Dict[str, Any]:
        raw = await file.read()
        sha = _sha256_bytes(raw)
        try:
            events.emit("ingest.started", {"type": "document", "sha256": sha, "filename": file.filename or ""})
        except Exception:
            pass
        existing = engine.db.get_file_ingest_by_sha256(sha)
        if existing and existing.get("status") == "success":
            return {
                "status": "skipped",
                "sha256": sha,
                "message": "Already ingested",
            }

        ingest_id = f"doc_{sha}"
        engine.db.upsert_file_ingest(
            ingest_id=ingest_id,
            source_type="document_upload",
            source_path=file.filename or "",
            source_sha256=sha,
            source_mtime=None,
            status="running",
            message=None,
        )

        # 解析domains和tags
        selected_domains = json.loads(domains) if domains else []
        selected_tags = json.loads(tags) if tags else []
        enable_auto_classify = auto_classify.lower() == "true"

        suffix = Path(file.filename or "").suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tmp.write(raw)
            tmp.flush()
            tmp.close()

            text = _extract_document_text(Path(tmp.name), doc_type)
            if not text:
                raise RuntimeError("No text extracted")

            now = datetime.utcnow()
            resolved_id = (case_id or "").strip() or f"case_{sha[:16]}"
            
            # 自动分类
            suggested_domains = []
            if enable_auto_classify and not domain and not selected_domains:
                classify_results = auto_classify_domain(text)
                if classify_results:
                    suggested_domains = [r["domain"] for r in classify_results[:3]]
                    selected_domains = [classify_results[0]["domain"]]
            
            resolved_domain = (domain or "").strip() or (selected_domains[0] if selected_domains else "general")
            resolved_title = (title or "").strip() or (Path(file.filename or "document").stem)

            if engine.db.case_exists(resolved_id):
                engine.db.upsert_file_ingest(
                    ingest_id=ingest_id,
                    source_type="document_upload",
                    source_path=file.filename or "",
                    source_sha256=sha,
                    source_mtime=None,
                    status="skipped",
                    imported_count=0,
                    skipped_count=1,
                    failed_count=0,
                    message=f"Case id already exists: {resolved_id}",
                )
                return {
                    "status": "skipped",
                    "sha256": sha,
                    "case_id": resolved_id,
                    "message": "Case id already exists",
                }

            from ..models.case import Case

            engine.add_case(
                Case(
                    id=resolved_id,
                    domain=resolved_domain,
                    title=resolved_title[:300],
                    description=(text[:8000] if text else "") or None,
                    tags=selected_tags,
                    created_at=now,
                    updated_at=now,
                )
            )

            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="document_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status="success",
                imported_count=1,
                skipped_count=0,
                failed_count=0,
                message=None,
            )
            try:
                events.emit(
                    "ingest.completed",
                    {"type": "document", "sha256": sha, "case_ids": [resolved_id], "status": "success"},
                )
            except Exception:
                pass
            return {
                "status": "success",
                "sha256": sha,
                "case_id": resolved_id,
                "auto_classified": enable_auto_classify and len(suggested_domains) > 0,
                "suggested_domains": suggested_domains if enable_auto_classify else None,
            }
        except Exception as e:
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="document_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status="failed",
                imported_count=0,
                skipped_count=0,
                failed_count=1,
                message=str(e),
            )
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            try:
                Path(tmp.name).unlink(missing_ok=True)
            except Exception:
                pass

    @app.post("/ingest/json")
    async def ingest_json(
        file: UploadFile = File(...),
        default_domain: str = Form(""),
        on_conflict: str = Form("skip"),
        auto_classify: str = Form("false"),
        domains: str = Form(""),
        tags: str = Form(""),
    ) -> Dict[str, Any]:
        raw = await file.read()
        sha = _sha256_bytes(raw)
        try:
            events.emit("ingest.started", {"type": "json", "sha256": sha, "filename": file.filename or ""})
        except Exception:
            pass
        existing = engine.db.get_file_ingest_by_sha256(sha)
        if existing and existing.get("status") == "success":
            return {
                "status": "skipped",
                "sha256": sha,
                "imported": int(existing.get("imported_count") or 0),
                "skipped": int(existing.get("skipped_count") or 0),
                "failed": int(existing.get("failed_count") or 0),
                "message": "Already ingested",
            }

        ingest_id = f"json_{sha}"
        engine.db.upsert_file_ingest(
            ingest_id=ingest_id,
            source_type="json_upload",
            source_path=file.filename or "",
            source_sha256=sha,
            source_mtime=None,
            status="running",
            message=None,
        )

        # 解析domains和tags
        selected_domains = json.loads(domains) if domains else []
        selected_tags = json.loads(tags) if tags else []
        enable_auto_classify = auto_classify.lower() == "true"
        
        # 如果用户选择了领域，使用第一个作为默认领域
        if selected_domains and not default_domain:
            default_domain = selected_domains[0]

        imported = 0
        skipped = 0
        failed = 0
        case_ids: List[str] = []
        suggested_domains: List[str] = []
        
        try:
            text = raw.decode("utf-8", errors="replace")
            payload_raw = __import__("json").loads(text)
            payload = _coerce_json_cases_payload(payload_raw)
            if not payload:
                raise RuntimeError("JSON must be an array of objects (or wrapped as {cases/items/data/rows: [...]})")

            headers: list[str] = []
            for obj in payload:
                if isinstance(obj, dict):
                    headers.extend([str(k) for k in obj.keys()])
            headers = list(dict.fromkeys(headers))

            column_map = _auto_column_map(headers)
            print(f"Headers: {headers}")
            print(f"Column map: {column_map}")

            from ..models.case import Case

            for idx, obj in enumerate(payload, start=1):
                try:
                    row = {str(k): _normalize_ingest_value(v) for k, v in obj.items()}
                    
                    # 如果启用自动分类且没有指定domain
                    domain_col = column_map.get("domain", "")
                    row_domain = row.get(domain_col, "") if domain_col else ""
                    if enable_auto_classify and not row_domain and not default_domain:
                        row_text = " ".join(str(v) for v in row.values() if v)
                        classify_results = auto_classify_domain(row_text)
                        if classify_results:
                            # 如果没有domain列，需要创建一个
                            if not domain_col:
                                domain_col = "domain"
                                column_map["domain"] = domain_col
                            row[domain_col] = classify_results[0]["domain"]
                            if classify_results[0]["domain"] not in suggested_domains:
                                suggested_domains.append(classify_results[0]["domain"])
                    
                    data = _build_case_from_row(
                        row, 
                        column_map=column_map, 
                        default_domain=default_domain,
                        tags=selected_tags,
                        auto_classify=enable_auto_classify
                    )
                    case_id = str(data["id"])
                    if on_conflict == "skip" and engine.db.case_exists(case_id):
                        skipped += 1
                        continue
                    engine.add_case(Case(**data))
                    imported += 1
                    case_ids.append(case_id)
                except Exception as e:
                    import traceback
                    print(f"Failed to import row {idx}: {e}")
                    print(traceback.format_exc())
                    failed += 1
                    continue

            status = "success" if failed == 0 else "partial"
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="json_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status=status,
                imported_count=imported,
                skipped_count=skipped,
                failed_count=failed,
                message=None,
            )

            # KG extraction handled by plugin via events
            try:
                events.emit(
                    "ingest.completed",
                    {"type": "json", "sha256": sha, "case_ids": case_ids, "status": status},
                )
            except Exception:
                pass
            return {
                "status": status,
                "sha256": sha,
                "imported": imported,
                "skipped": skipped,
                "failed": failed,
                "case_ids": case_ids,
                "auto_classified": enable_auto_classify and len(suggested_domains) > 0,
                "suggested_domains": suggested_domains if enable_auto_classify else None,
            }
        except Exception as e:
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="json_upload",
                source_path=file.filename or "",
                source_sha256=sha,
                source_mtime=None,
                status="failed",
                imported_count=imported,
                skipped_count=skipped,
                failed_count=max(1, failed),
                message=str(e),
            )
            try:
                events.emit("ingest.failed", {"type": "json", "sha256": sha, "error": str(e)})
            except Exception:
                pass
            raise HTTPException(status_code=400, detail=str(e))

    # ========== 异步导入 API ==========
    
    @app.post("/ingest/json/async")
    async def ingest_json_async(
        file: UploadFile = File(...),
        default_domain: str = Form(""),
        auto_classify: str = Form("false"),
        auto_cluster: str = Form("false"),
        domains: str = Form(""),
        tags: str = Form(""),
    ) -> Dict[str, Any]:
        """
        异步 JSON 导入 - 立即返回任务ID，后台执行 AI 分析
        """
        import uuid
        from ..core.async_importer import AsyncImporter
        
        raw = await file.read()
        
        # 解析 JSON
        try:
            text = raw.decode("utf-8", errors="replace")
            payload_raw = json.loads(text)
            payload = _coerce_json_cases_payload(payload_raw)
            if not payload:
                raise RuntimeError("JSON must be an array of objects (or wrapped as {cases/items/data/rows: [...]})")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
        
        # 解析参数
        selected_domains = json.loads(domains) if domains else []
        selected_tags = json.loads(tags) if tags else []
        enable_auto_classify = auto_classify.lower() == "true"
        enable_auto_cluster = auto_cluster.lower() == "true"
        
        if selected_domains and not default_domain:
            default_domain = selected_domains[0]
        
        # 转换数据格式
        headers: list[str] = []
        for obj in payload:
            if isinstance(obj, dict):
                headers.extend([str(k) for k in obj.keys()])
        headers = list(dict.fromkeys(headers))
        column_map = _auto_column_map(headers)
        
        cases_data = []
        for obj in payload:
            row = {str(k): _normalize_ingest_value(v) for k, v in obj.items()}
            try:
                data = _build_case_from_row(
                    row,
                    column_map=column_map,
                    default_domain=default_domain,
                    tags=selected_tags,
                    auto_classify=False,  # 不在此处分类，交给异步任务
                )
                cases_data.append(data)
            except Exception as e:
                print(f"Failed to build case: {e}")
        
        # 创建异步导入任务
        task_id = f"import_{uuid.uuid4().hex[:12]}"
        importer = AsyncImporter(engine.db.path)
        
        importer.start_import(
            task_id=task_id,
            cases_data=cases_data,
            enable_ai_classify=enable_auto_classify,
            enable_ai_clustering=enable_auto_cluster,
            default_domain=default_domain
        )
        
        return {
            "status": "started",
            "task_id": task_id,
            "total_cases": len(cases_data),
            "message": "导入任务已启动，请使用 /tasks/{task_id} 查询进度"
        }
    
    @app.get("/tasks/{task_id}")
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """查询导入任务状态"""
        from ..core.async_importer import AsyncImporter
        
        importer = AsyncImporter(engine.db.path)
        task = importer.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        total_cases = int(task.get("total_cases") or 0)
        processed_cases = int(task.get("processed_cases") or 0)

        stage = str(task.get("stage") or "import")
        stage_done = int(task.get("stage_done") or 0)
        stage_total = int(task.get("stage_total") or 0)

        denom = max(total_cases, 1)
        pct = (processed_cases / denom) * 100 if total_cases > 0 else 0
        if pct < 0:
            pct = 0
        if pct > 100:
            pct = 100

        # Don't show 100% while still processing (AI steps may continue after import)
        try:
            status = str(task.get("status") or "")
        except Exception:
            status = ""
        if status == "processing" and total_cases > 0 and processed_cases >= total_cases:
            pct = min(pct, 99.0)
        if status == "completed":
            pct = 100

        # Weighted overall percent based on stages
        # import 35% + classify 20% + kg_extract 45%
        weights = {"import": 0.35, "classify": 0.20, "kg_extract": 0.45}
        def frac(done: int, total: int) -> float:
            if total <= 0:
                return 0.0
            return max(0.0, min(1.0, float(done) / float(total)))

        import_frac = frac(processed_cases, total_cases)
        classify_frac = frac(stage_done, stage_total) if stage == "classify" else 0.0
        kg_frac = frac(stage_done, stage_total) if stage == "kg_extract" else 0.0
        if stage == "completed":
            overall = 100.0
        else:
            overall = (import_frac * weights["import"] + classify_frac * weights["classify"] + kg_frac * weights["kg_extract"]) * 100.0
            overall = max(0.0, min(99.0, overall))

        return {
            "task_id": task_id,
            "status": task["status"],
            "total_cases": total_cases,
            "processed_cases": processed_cases,
            "stage": stage,
            "stage_done": stage_done,
            "stage_total": stage_total,
            "current_case": task["current_case"],
            "current_action": task["current_action"],
            "progress_percent": round(pct, 1),
            "overall_percent": round(overall, 1),
            "stages": {
                "import": {"done": processed_cases, "total": total_cases},
                "classify": {"done": stage_done if stage == "classify" else 0, "total": stage_total if stage == "classify" else int(task.get("stage_total") or 0)},
                "kg_extract": {"done": stage_done if stage == "kg_extract" else 0, "total": stage_total if stage == "kg_extract" else int(task.get("stage_total") or 0)},
            },
            "result": task.get("result"),
            "error_message": task.get("error_message"),
            "created_at": task["created_at"],
            "updated_at": task["updated_at"]
        }
    
    @app.get("/tasks")
    def list_active_tasks() -> Dict[str, Any]:
        """列出活跃的导入任务"""
        from ..storage.task_store import get_task_store
        
        task_store = get_task_store(engine.db.path)
        # 这里简化处理，实际应该查询所有任务
        return {
            "message": "使用 /tasks/{task_id} 查询特定任务"
        }

    @app.post("/query", response_model=QueryResponse)
    def query(req: QueryRequest = Body(...)) -> QueryResponse:
        mode = (req.mode or "").strip().lower()
        if mode in {"graphrag", "graph_rag", "graph"}:
            try:
                from ..graphrag.service import GraphRAGService

                svc = GraphRAGService(
                    config=engine.config,
                    db=engine.db,
                    ai=engine.ai_assistant,
                    hot_index=hot_index,
                    kg_store=kg_store,
                )
                r = svc.query(text=req.text, top_k=int(engine.config.get("graphrag.retrieval.top_k", 20) or 20))
                return QueryResponse(
                    matches=len(r.cases),
                    cases=[c.model_dump() for c in r.cases],
                    reasoning=r.reasoning,
                    recommendations=list(r.recommendations),
                )
            except Exception:
                # fall back to classic retrieval
                pass

        result = engine.query(req.text)
        return QueryResponse(
            matches=len(result.cases),
            cases=[c.model_dump() for c in result.cases],
            reasoning=result.reasoning,
            recommendations=list(result.recommendations),
        )

    @app.post("/graphrag/index")
    def graphrag_index(limit_cases: int = Body(0)) -> Dict[str, Any]:
        """Build/refresh GraphRAG vector index in Qdrant."""
        try:
            from ..graphrag.service import GraphRAGService

            svc = GraphRAGService(
                config=engine.config,
                db=engine.db,
                ai=engine.ai_assistant,
                hot_index=hot_index,
                kg_store=kg_store,
            )
            return svc.index_cases(limit=int(limit_cases or 0))
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.get("/graphrag/status")
    def graphrag_status() -> Dict[str, Any]:
        """Diagnose GraphRAG runtime: qdrant connectivity, collection status, and embedding health."""
        out: Dict[str, Any] = {
            "enabled": bool(engine.config.get("graphrag.enabled", True)),
            "qdrant": {},
            "embedding": {},
        }

        qcfg = engine.config.get("graphrag.qdrant", {}) or {}
        ecfg = engine.config.get("graphrag.embedding", {}) or {}
        out["qdrant"]["url"] = str(qcfg.get("url") or "")
        out["qdrant"]["collection"] = str(qcfg.get("collection") or "")
        out["embedding"]["provider"] = str(ecfg.get("provider") or "")
        out["embedding"]["model"] = str(ecfg.get("model") or "")
        out["embedding"]["api_base_set"] = bool(str(ecfg.get("api_base") or "").strip())
        out["embedding"]["api_key_set"] = bool(str(ecfg.get("api_key") or "").strip())

        try:
            from ..graphrag.service import GraphRAGService

            svc = GraphRAGService(
                config=engine.config,
                db=engine.db,
                ai=engine.ai_assistant,
                hot_index=hot_index,
                kg_store=kg_store,
            )

            # embedding smoke test
            try:
                v = svc._embedder.embed("hello")  # type: ignore[attr-defined]
                out["embedding"]["ok"] = bool(v)
                out["embedding"]["dim"] = len(v) if isinstance(v, list) else 0
            except Exception as e:
                out["embedding"]["ok"] = False
                out["embedding"]["error"] = str(e)

            # qdrant connectivity + collection stats
            try:
                store = svc._store()  # type: ignore[attr-defined]
                client = store._client  # type: ignore[attr-defined]
                out["qdrant"]["reachable"] = True
                try:
                    cols = client.get_collections().collections
                    out["qdrant"]["collections"] = [c.name for c in cols]
                    col = store._collection  # type: ignore[attr-defined]
                    out["qdrant"]["collection_exists"] = any(c.name == col for c in cols)
                except Exception as e:
                    out["qdrant"]["collections_error"] = str(e)

                try:
                    info = client.get_collection(store._collection)  # type: ignore[attr-defined]
                    out["qdrant"]["points_count"] = int(getattr(info, "points_count", 0) or 0)
                    cfg = getattr(info, "config", None)
                    vs = None
                    if cfg and getattr(cfg, "params", None) and getattr(cfg.params, "vectors", None):
                        vs = getattr(cfg.params.vectors, "size", None)
                    out["qdrant"]["vector_size"] = int(vs) if vs else None
                except Exception as e:
                    out["qdrant"]["collection_info_error"] = str(e)
            except Exception as e:
                out["qdrant"]["reachable"] = False
                out["qdrant"]["error"] = str(e)

        except Exception as e:
            out["error"] = str(e)

        return out

    @app.post("/decisions")
    def log_decision(req: DecisionLogRequest) -> Dict[str, str]:
        decision_id = req.id or f"dec_{uuid.uuid4().hex[:12]}"
        log_entry = DecisionLog(
            id=decision_id,
            query=req.query,
            context=req.context,
            recommended_cases=req.recommended_cases,
            user_decision=req.choice,
            predicted_outcome=req.predict,
            created_at=datetime.utcnow(),
            evaluated_at=None,
        )
        engine.log_decision(log_entry)
        return {"id": log_entry.id}

    @app.post("/decisions/{decision_id}/evaluate")
    def evaluate_decision(decision_id: str, req: EvaluateDecisionRequest) -> Dict[str, str]:
        try:
            engine.evaluate_decision(decision_id=decision_id, actual_outcome=req.outcome)
        except KeyError:
            raise HTTPException(status_code=404, detail="decision not found")
        return {"id": decision_id}

    # AI配置相关API
    @app.get("/ai/config")
    def get_ai_config() -> Dict[str, Any]:
        """获取当前AI配置（不包含敏感信息）"""
        return {
            "provider": engine.config.get("ai.provider", "ollama"),
            "model": engine.config.get("ai.model", "qwen3.5:4b"),
            "api_base": engine.config.get("ai.api_base", ""),
            "api_key_set": bool(engine.config.get("ai.api_key", "")),
        }

    @app.get("/debug/db")
    def debug_db() -> Dict[str, Any]:
        """Debug helper: show actual sqlite path and row counts.

        This helps verify which database file the running server is using.
        """
        out: Dict[str, Any] = {
            "db_path": str(getattr(engine.db, "path", "")),
            "counts": {},
        }
        try:
            conn = engine.db.connect()
            cur = conn.cursor()
            for t in ["cases", "entities", "relations", "relation_evidence", "kg_case_state"]:
                try:
                    n = cur.execute(f"SELECT count(1) FROM {t}").fetchone()[0]
                    out["counts"][t] = int(n)
                except Exception as e:
                    out["counts"][t] = f"ERR: {e}"
        except Exception as e:
            out["error"] = str(e)
        return out

    @app.post("/ai/config")
    def update_ai_config(
        provider: str = Body("ollama"),
        model: str = Body("qwen3.5:4b"),
        api_key: str = Body(""),
        api_base: str = Body(""),
    ) -> Dict[str, str]:
        """更新AI配置"""
        try:
            engine.update_ai_config(
                provider=provider,
                model=model,
                api_key=api_key if api_key else None,
                api_base=api_base if api_base else None,
            )
            return {
                "status": "success",
                "provider": provider,
                "model": model,
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/ai/status")
    def get_ai_status() -> Dict[str, Any]:
        """获取AI服务状态"""
        return {
            "available": engine.ai_assistant.check_available(),
            "provider": engine.ai_assistant.provider,
            "model": engine.ai_assistant.model,
        }

    return app
