from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from ..ai.decision_assistant import AIDecisionAssistant
from ..utils.helpers import utc_now


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _canon_entity_type(t: str) -> str:
    tt = (t or "").strip().lower()
    if tt in {"crash", "market_crash", "crisis", "股灾", "股灾名称", "崩盘"}:
        return "Crash"
    if tt in {"risk", "risk_type", "risk-type", "风险", "风险类型", "risktype"}:
        return "RiskType"
    if tt in {"event", "事件", "trigger", "policy_event", "政策事件"}:
        return "Event"
    if tt in {"org", "organization", "机构", "公司"}:
        return "Org"
    if tt in {"person", "人物", "个人"}:
        return "Person"
    if tt in {"indicator", "指标"}:
        return "Indicator"
    if tt in {"policy", "政策"}:
        return "Policy"
    if tt in {"place", "地点", "国家", "地区"}:
        return "Place"
    if tt in {"concept", "概念"}:
        return "Concept"
    return "Entity"


def _canon_relation_type(t: str) -> str:
    tt = (t or "").strip().lower()
    if tt in {"has_risk_type", "risk_type", "风险类型", "属于风险"}:
        return "HAS_RISK_TYPE"
    if tt in {"triggered_by", "trigger", "导火索", "触发"}:
        return "TRIGGERED_BY"
    if tt in {"caused", "cause", "causes", "导致"}:
        return "CAUSED"
    if tt in {"leads_to", "lead_to", "引发", "导致发生"}:
        return "LEADS_TO"
    if tt in {"part_of", "belongs_to", "组成"}:
        return "PART_OF"
    if tt in {"used_for", "用于"}:
        return "USED_FOR"
    return "RELATED_TO"


def _entity_id(entity_type: str, name: str) -> str:
    et = _canon_entity_type(entity_type)
    key = f"{et.strip().lower()}::{name.strip().lower()}"
    prefix = (
        "crash"
        if et == "Crash"
        else "risk"
        if et == "RiskType"
        else "event"
        if et == "Event"
        else "ent"
    )
    return f"{prefix}_{_sha1(key)[:16]}"


def _relation_id(source_entity_id: str, relation_type: str, target_entity_id: str, quote: str) -> str:
    rt = _canon_relation_type(relation_type)
    q = (quote or "").strip().lower()
    key = f"{source_entity_id}::{rt.strip().lower()}::{target_entity_id}::{q}"
    return f"rel_{_sha1(key)[:16]}"


def _normalize_and_dedupe(
    entities: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    ent_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for e in entities:
        name = str(e.get("name") or "").strip()
        if not name:
            continue
        et = _canon_entity_type(str(e.get("type") or ""))
        key = (et, name.lower())
        existing = ent_by_key.get(key)
        if existing is None:
            eid = _entity_id(et, name)
            ent_by_key[key] = {
                "id": eid,
                "name": name,
                "type": et,
                "attributes": e.get("attributes") if isinstance(e.get("attributes"), dict) else {},
                "updated_at": e.get("updated_at") or utc_now(),
            }
        else:
            # merge attributes best-effort
            attrs = e.get("attributes") if isinstance(e.get("attributes"), dict) else {}
            if attrs:
                merged = dict(existing.get("attributes") or {})
                for k, v in attrs.items():
                    if k not in merged:
                        merged[k] = v
                existing["attributes"] = merged

    id_by_key = {k: v["id"] for k, v in ent_by_key.items()}

    rel_seen: set[Tuple[str, str, str]] = set()
    rel_out: List[Dict[str, Any]] = []
    for r in relations:
        src = str(r.get("source") or "").strip()
        tgt = str(r.get("target") or "").strip()
        if not src or not tgt:
            continue
        rt = _canon_relation_type(str(r.get("relation_type") or r.get("type") or ""))
        quote = str(r.get("quote") or "").strip()[:320]
        key = (src, rt, tgt)
        if key in rel_seen:
            continue
        rel_seen.add(key)
        rid = _relation_id(src, rt, tgt, quote)
        conf = r.get("confidence")
        try:
            confidence = float(conf)
        except Exception:
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        rel_out.append(
            {
                "id": rid,
                "source": src,
                "target": tgt,
                "relation_type": rt,
                "confidence": confidence,
                "quote": quote,
                "case_id": r.get("case_id"),
                "updated_at": r.get("updated_at") or utc_now(),
            }
        )

    return list(ent_by_key.values()), rel_out


def extract_kg_from_case(
    ai: AIDecisionAssistant,
    *,
    case_id: str,
    title: str,
    domain: str,
    text: str,
    timeout_hint: int = 60,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    prompt = f"""你是一个知识图谱构建助手。请从给定的案例文本中抽取实体(Entity)和关系(Relation)。

要求：
- 只抽取高价值信息，宁可少抽取
- 实体 type 必须从以下枚举中选择：
  - Crash（股灾/市场崩盘/危机事件名称）
  - RiskType（风险类型，如“流动性风险/杠杆风险/政策风险”）
  - Event（触发事件/导火索/政策事件）
  - Org, Person, Indicator, Policy, Place, Concept
  - Entity（其他）
- 关系 relation_type 必须从以下枚举中选择：
  - HAS_RISK_TYPE（Crash -> RiskType）
  - TRIGGERED_BY（Crash -> Event）
  - CAUSED（Event/Factor -> Crash 或 Crash -> Crash）
  - LEADS_TO, PART_OF, USED_FOR, RELATED_TO
- quote 尽量能在原文中找到并尽量短（<= 120 字）。如果确实找不到，可留空字符串，但仍然要输出关系。
- 限制数量：entities 最多 20 个，relations 最多 25 条

请只输出 JSON（不要输出多余文字）。必须包含两个字段：
1) entities: 数组，每个元素包含 name,type,attributes(可选对象)
2) relations: 数组，每个元素包含 source_name,source_type,relation_type,target_name,target_type,confidence(0-1),quote

案例ID: {case_id}
领域: {domain}
标题: {title}

文本:
{text[:6000]}
"""

    raw = ai._call_ai(prompt)
    if not raw:
        return [], []

    try:
        data = json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(raw[start : end + 1])
        else:
            return [], []

    entities_in = data.get("entities") or []
    relations_in = data.get("relations") or []

    entities: List[Dict[str, Any]] = []
    for e in entities_in:
        try:
            name = str(e.get("name") or "").strip()
            et = _canon_entity_type(str(e.get("type") or "").strip() or "Entity")
            if not name:
                continue
            eid = _entity_id(et, name)
            attrs = e.get("attributes")
            if not isinstance(attrs, dict):
                attrs = {}
            entities.append(
                {
                    "id": eid,
                    "name": name,
                    "type": et,
                    "attributes": attrs,
                    "updated_at": utc_now(),
                }
            )
        except Exception:
            continue

    ent_map: Dict[Tuple[str, str], str] = {(e["type"], e["name"]): e["id"] for e in entities}

    relations: List[Dict[str, Any]] = []
    for r in relations_in:
        try:
            sn = str(r.get("source_name") or "").strip()
            st = _canon_entity_type(str(r.get("source_type") or "").strip() or "Entity")
            tn = str(r.get("target_name") or "").strip()
            tt = _canon_entity_type(str(r.get("target_type") or "").strip() or "Entity")
            rt = _canon_relation_type(str(r.get("relation_type") or "").strip() or "RELATED_TO")
            quote = str(r.get("quote") or "").strip()[:320]
            conf = r.get("confidence")
            try:
                confidence = float(conf)
            except Exception:
                confidence = 0.5
            confidence = max(0.0, min(1.0, confidence))

            if not sn or not tn:
                continue

            se = ent_map.get((st, sn))
            if not se:
                se = _entity_id(st, sn)
                ent_map[(st, sn)] = se
                entities.append({"id": se, "name": sn, "type": st, "attributes": {}, "updated_at": utc_now()})

            te = ent_map.get((tt, tn))
            if not te:
                te = _entity_id(tt, tn)
                ent_map[(tt, tn)] = te
                entities.append({"id": te, "name": tn, "type": tt, "attributes": {}, "updated_at": utc_now()})

            rid = _relation_id(se, rt, te, quote)
            relations.append(
                {
                    "id": rid,
                    "source": se,
                    "target": te,
                    "relation_type": rt,
                    "confidence": confidence,
                    "quote": quote,
                    "case_id": case_id,
                    "updated_at": utc_now(),
                }
            )
        except Exception:
            continue

    return _normalize_and_dedupe(entities, relations)
