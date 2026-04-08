from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ..core.llm import LLMService
from ..core.events import events
from ..utils.logger import get_logger
from ..ai.redteam import RedTeam
from .base import Plugin, PluginInfo
from .evidence_builder import build_evidence


log = get_logger("vintagewisdom.plugins.ai_redteam_llm")


class AIRedTeamLLMPlugin(Plugin):
    INFO = PluginInfo(
        name="ai.redteam.llm",
        version="0.1.0",
        description="LLM red-team critique with evidence references",
        author="VintageWisdom",
        dependencies=[],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)
        self._llm: Optional[LLMService] = None
        self._fallback = RedTeam()

    def initialize(self) -> None:
        events.on("decision.after", self._on_decision_after)

    def _on_decision_after(self, event) -> None:
        try:
            mode = str(self.app.config.get("plugins.config.ai.redteam.mode", "llm") or "llm").lower()
            if mode != "llm":
                return

            data = event.data or {}
            text = str(data.get("text") or "")
            if not text.strip():
                return

            evidence = data.get("evidence")
            if not isinstance(evidence, dict):
                evidence_cfg = self.app.config.get("plugins.config.evidence.builder", {}) or {}
                evidence = build_evidence(
                    text=text,
                    cases=data.get("cases") if isinstance(data.get("cases"), list) else [],
                    engine=getattr(self.app, "engine", None),
                    config=evidence_cfg if isinstance(evidence_cfg, dict) else {},
                )
                data["evidence"] = evidence

            critique = self._run_llm_redteam(text, evidence)
            if not critique:
                critique = self._fallback.run(text)
                if critique:
                    reasoning = str(data.get("reasoning") or "")
                    data["reasoning"] = (reasoning + "\n\n[RedTeam]\n" + critique).strip()
                return

            reasoning = str(data.get("reasoning") or "")
            data["reasoning"] = (reasoning + "\n\n[RedTeam-LLM]\n" + critique).strip()

            checklist = self._extract_checklist(critique)
            if checklist:
                recs = data.get("recommendations")
                if not isinstance(recs, list):
                    recs = []
                max_recs = int(self.config.get("max_recommendations", 6) or 6)
                for item in checklist:
                    if len(recs) >= max_recs:
                        break
                    if item and item not in recs:
                        recs.append(item)
                data["recommendations"] = recs
        except Exception as e:
            log.error("ai.redteam.llm failed: %s", e)
            return

    def _ensure_llm(self) -> Optional[LLMService]:
        if self._llm is not None:
            return self._llm
        try:
            cfg = self.app.config
            self._llm = LLMService(
                provider=cfg.get("ai.provider", "ollama"),
                model=cfg.get("ai.model", "qwen3.5:4b"),
                api_key=cfg.get("ai.api_key", ""),
                api_base=cfg.get("ai.api_base", ""),
                timeout_s=int(cfg.get("ai.timeout_s", 30) or 30),
                retries=int(cfg.get("ai.retries", 1) or 1),
            )
            return self._llm
        except Exception:
            self._llm = None
            return None

    def _run_llm_redteam(self, text: str, evidence: Dict[str, Any]) -> str:
        llm = self._ensure_llm()
        if not llm or not llm.check_available():
            return ""

        prompt = _build_redteam_prompt(text, evidence)
        raw = llm.generate(prompt, temperature=0.3, timeout_s=60)
        if not raw:
            return ""

        data = _parse_json_block(raw)
        if not isinstance(data, dict):
            return ""

        return _render_layers(data, max_layers=int(self.config.get("max_layers", 6) or 6))

    def _extract_checklist(self, critique: str) -> List[str]:
        out: List[str] = []
        for line in (critique or "").splitlines():
            line = line.strip()
            if not line or line.startswith("["):
                continue
            if line.startswith("-"):
                item = line.lstrip("-").strip()
                if item:
                    out.append(item)
        return out[:12]


def _build_redteam_prompt(text: str, evidence: Dict[str, Any]) -> str:
    cases = evidence.get("cases") if isinstance(evidence, dict) else []
    snippets = evidence.get("snippets") if isinstance(evidence, dict) else []
    kg_paths = evidence.get("kg_paths") if isinstance(evidence, dict) else []

    parts: List[str] = []
    parts.append("You are a red-team reviewer. Use ONLY the evidence below.")
    parts.append("Return JSON with schema: {\"layers\": [{\"type\": \"facts|logic|assumptions|worst_case|opportunity_cost|reversibility\", \"questions|attacks|assumptions|scenario|mitigation|alternatives|steps\": [...], \"evidence_refs\": [\"case:...\", \"snippet:...\", \"kg:...\"]}]}")
    parts.append("")
    parts.append("Decision Query:")
    parts.append(text.strip())
    parts.append("")

    if isinstance(cases, list) and cases:
        parts.append("Case Evidence:")
        for c in cases:
            if not isinstance(c, dict):
                continue
            cid = c.get("id") or ""
            title = c.get("title") or ""
            lesson = (c.get("lesson_core") or "")[:200]
            outcome = (c.get("outcome_result") or "")[:200]
            parts.append(f"- case:{cid} | {title} | lesson: {lesson} | outcome: {outcome}")

    if isinstance(snippets, list) and snippets:
        parts.append("")
        parts.append("Snippet Evidence:")
        for i, s in enumerate(snippets[:8], start=1):
            if not isinstance(s, dict):
                continue
            cid = s.get("case_id") or ""
            text_snip = (s.get("text") or "")[:240]
            parts.append(f"- snippet:{cid}:{i} | {text_snip}")

    if isinstance(kg_paths, list) and kg_paths:
        parts.append("")
        parts.append("KG Evidence:")
        for i, p in enumerate(kg_paths[:8], start=1):
            if not isinstance(p, dict):
                continue
            path = p.get("path") or ""
            parts.append(f"- kg:{i} | {path}")

    parts.append("")
    parts.append("Return ONLY JSON. Each layer must include evidence_refs.")
    return "\n".join([p for p in parts if p is not None])


def _parse_json_block(raw: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except Exception:
                return None
    return None


def _render_layers(data: Dict[str, Any], max_layers: int = 6) -> str:
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        return ""
    out: List[str] = []
    for layer in layers[:max_layers]:
        if not isinstance(layer, dict):
            continue
        ltype = str(layer.get("type") or "").strip()
        evidence_refs = layer.get("evidence_refs")
        refs = []
        if isinstance(evidence_refs, list):
            refs = [str(r) for r in evidence_refs if str(r).strip()]
        ref_text = f" (evidence: {', '.join(refs)})" if refs else ""

        if ltype == "facts":
            questions = _as_list(layer.get("questions"))
            for q in questions:
                out.append(f"- Facts: {q}{ref_text}")
        elif ltype == "logic":
            attacks = _as_list(layer.get("attacks"))
            for a in attacks:
                out.append(f"- Logic: {a}{ref_text}")
        elif ltype == "assumptions":
            assumptions = _as_list(layer.get("assumptions"))
            for a in assumptions:
                out.append(f"- Assumptions: {a}{ref_text}")
        elif ltype == "worst_case":
            scenario = str(layer.get("scenario") or "").strip()
            mitigations = _as_list(layer.get("mitigation"))
            if scenario:
                out.append(f"- WorstCase: {scenario}{ref_text}")
            for m in mitigations:
                out.append(f"- Mitigation: {m}{ref_text}")
        elif ltype == "opportunity_cost":
            alternatives = _as_list(layer.get("alternatives"))
            for alt in alternatives:
                out.append(f"- OpportunityCost: {alt}{ref_text}")
        elif ltype == "reversibility":
            steps = _as_list(layer.get("steps"))
            for s in steps:
                out.append(f"- Reversibility: {s}{ref_text}")
    return "\n".join(out).strip()


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
