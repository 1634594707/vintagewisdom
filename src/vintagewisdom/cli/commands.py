from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from urllib.request import Request, urlopen

from ..core.engine import Engine
from ..models.case import Case
from ..models.decision import DecisionLog
from ..utils.helpers import utc_now
from ..utils.logger import get_logger
import yaml


log = get_logger("vintagewisdom.cli")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vw", description="VintageWisdom CLI")
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize local data storage")

    sub.add_parser("tui", help="Interactive TUI (REPL)")

    query = sub.add_parser("query", help="Query similar cases")
    query.add_argument("text", nargs="+", help="Query text")

    add_case = sub.add_parser("add-case", help="Add a new case")
    add_case.add_argument("--id", required=True)
    add_case.add_argument("--domain", required=True)
    add_case.add_argument("--title", required=True)
    add_case.add_argument("--description", default="")
    add_case.add_argument("--decision-node", default="")
    add_case.add_argument("--action-taken", default="")
    add_case.add_argument("--outcome-result", default="")
    add_case.add_argument("--outcome-timeline", default="")
    add_case.add_argument("--lesson-core", default="")
    add_case.add_argument("--confidence", default="")

    log_decision = sub.add_parser("log-decision", help="Log a decision (start the loop)")
    log_decision.add_argument("--id", required=True)
    log_decision.add_argument("--query", required=True, help="Decision question / query")
    log_decision.add_argument("--context", default="", help="Optional context (free text)")
    log_decision.add_argument("--choice", default="", help="Your choice (optional)")
    log_decision.add_argument(
        "--predict",
        default="",
        help="Predicted outcome (optional)",
    )

    eval_decision = sub.add_parser(
        "evaluate-decision", help="Evaluate a decision (fill actual outcome)"
    )
    eval_decision.add_argument("--id", required=True)
    eval_decision.add_argument("--outcome", required=True, help="Actual outcome")

    import_csv = sub.add_parser("import-csv", help="Import cases from a CSV file")
    import_csv.add_argument("--file", required=True, help="Path to CSV file")
    import_csv.add_argument(
        "--mapping",
        default="",
        help="Optional mapping file (YAML/JSON) for column-to-field mapping",
    )
    import_csv.add_argument(
        "--default-domain",
        default="",
        help="Default domain when CSV has no domain column",
    )
    import_csv.add_argument(
        "--on-conflict",
        choices=["skip", "replace"],
        default="skip",
        help="When case id already exists in DB",
    )
    import_csv.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate only; do not write to database",
    )
    import_csv.add_argument(
        "--llm",
        choices=["", "api"],
        default="",
        help="Optional LLM backend for cleanup/extraction during import",
    )
    import_csv.add_argument(
        "--api-base",
        default="",
        help="API base URL (OpenAI-compatible, e.g. https://api.openai.com/v1)",
    )
    import_csv.add_argument(
        "--llm-model",
        default="",
        help="LLM model name (e.g. gpt-4.1-mini)",
    )
    import_csv.add_argument(
        "--llm-mode",
        choices=["extract", "normalize"],
        default="extract",
        help="extract: build Case from raw text; normalize: clean/standardize existing mapped fields",
    )

    scan_csv = sub.add_parser(
        "scan-csv",
        help="Auto scan a directory and import new CSV files (idempotent by file sha256)",
    )
    scan_csv.add_argument("--dir", required=True, help="Directory to scan")
    scan_csv.add_argument(
        "--pattern",
        default="*.csv",
        help="Glob pattern under directory (default: *.csv)",
    )
    scan_csv.add_argument(
        "--interval",
        type=float,
        default=10.0,
        help="Scan interval seconds when running continuously (default: 10)",
    )
    scan_csv.add_argument(
        "--once",
        action="store_true",
        help="Scan once and exit",
    )
    scan_csv.add_argument(
        "--mapping",
        default="",
        help="Optional mapping file (YAML/JSON) for column-to-field mapping",
    )
    scan_csv.add_argument(
        "--default-domain",
        default="",
        help="Default domain when CSV has no domain column",
    )
    scan_csv.add_argument(
        "--on-conflict",
        choices=["skip", "replace"],
        default="skip",
        help="When case id already exists in DB",
    )
    scan_csv.add_argument(
        "--llm",
        choices=["", "api"],
        default="",
        help="Optional LLM backend for cleanup/extraction during import",
    )
    scan_csv.add_argument(
        "--api-base",
        default="",
        help="API base URL (OpenAI-compatible, e.g. https://api.openai.com/v1)",
    )
    scan_csv.add_argument(
        "--llm-model",
        default="",
        help="LLM model name (e.g. gpt-4.1-mini)",
    )
    scan_csv.add_argument(
        "--llm-mode",
        choices=["extract", "normalize"],
        default="extract",
        help="extract: build Case from raw text; normalize: clean/standardize existing mapped fields",
    )

    ingest_dir = sub.add_parser(
        "ingest-dir",
        help="Batch ingest a directory (csv/json/md/pdf/docx/html/txt)",
    )
    ingest_dir.add_argument("--dir", required=True, help="Directory to scan")
    ingest_dir.add_argument(
        "--pattern",
        default="**/*",
        help="Glob pattern under directory (default: **/*)",
    )
    ingest_dir.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Worker threads for parsing (default: 4)",
    )
    ingest_dir.add_argument(
        "--mapping",
        default="",
        help="Optional mapping file (YAML/JSON) for CSV/JSON column-to-field mapping",
    )
    ingest_dir.add_argument(
        "--default-domain",
        default="",
        help="Default domain when missing in files",
    )
    ingest_dir.add_argument(
        "--on-conflict",
        choices=["skip", "replace"],
        default="skip",
        help="When case id already exists in DB",
    )
    ingest_dir.add_argument(
        "--llm",
        choices=["", "api"],
        default="",
        help="Optional LLM backend for cleanup/extraction during CSV import",
    )
    ingest_dir.add_argument(
        "--api-base",
        default="",
        help="API base URL (OpenAI-compatible, e.g. https://api.openai.com/v1)",
    )
    ingest_dir.add_argument(
        "--llm-model",
        default="",
        help="LLM model name (e.g. gpt-4.1-mini)",
    )
    ingest_dir.add_argument(
        "--llm-mode",
        choices=["extract", "normalize"],
        default="extract",
        help="extract: build Case from raw text; normalize: clean/standardize existing mapped fields",
    )
    ingest_dir.add_argument(
        "--tabular",
        action="store_true",
        help="Use pandas-based normalization for CSV/JSON before mapping",
    )

    ingest_doc = sub.add_parser(
        "ingest-doc",
        help="Extract text from PDF/DOCX and ingest into case database (idempotent by file sha256)",
    )
    ingest_doc.add_argument("--file", required=True, help="Path to PDF/DOCX")
    ingest_doc.add_argument(
        "--type",
        choices=["auto", "pdf", "docx"],
        default="auto",
        help="Document type (default: auto)",
    )
    ingest_doc.add_argument(
        "--id",
        default="",
        help="Optional case id; if empty, will be generated from file sha256",
    )
    ingest_doc.add_argument(
        "--domain",
        default="career",
        help="Case domain when not using LLM extraction (default: career)",
    )
    ingest_doc.add_argument(
        "--title",
        default="",
        help="Optional title when not using LLM extraction (default: file stem)",
    )
    ingest_doc.add_argument(
        "--llm",
        choices=["", "api"],
        default="",
        help="Optional LLM backend for extraction into structured Case",
    )
    ingest_doc.add_argument(
        "--api-base",
        default="",
        help="API base URL (OpenAI-compatible, e.g. https://api.openai.com/v1)",
    )
    ingest_doc.add_argument(
        "--llm-model",
        default="",
        help="LLM model name (e.g. gpt-4.1-mini)",
    )

    sub.add_parser("stats", help="Show basic stats")

    return parser


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


def _coerce_json_cases_payload(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("cases", "items", "data", "rows"):
            v = payload.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        return [payload]
    return []


def _normalize_rows_with_tabular(rows: list[dict]) -> list[dict]:
    if not rows:
        return rows
    try:
        from ..plugins.ingest_tabular import IngestTabularPlugin

        plugin = IngestTabularPlugin(app=None, config={})
        import pandas as pd  # type: ignore

        df = pd.DataFrame(rows)
        df = plugin.normalize_dataframe(df)
        return df.to_dict(orient="records")
    except Exception as e:
        log.error("Tabular normalization failed, falling back: %s", e)
        return rows


def _load_mapping(path: str) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text) or {}
    elif suffix == ".json":
        data = json.loads(text) or {}
    else:
        raise ValueError(f"Unsupported mapping file type: {p.suffix}")
    if not isinstance(data, dict):
        raise ValueError("Mapping file must be a dict")
    return data


def _auto_column_map(headers: list[str]) -> Dict[str, str]:
    normalized = {_normalize_header(h): h for h in headers}

    def pick(*candidates: str) -> str | None:
        for c in candidates:
            if c in normalized:
                return normalized[c]
        return None

    mapping: Dict[str, str] = {}
    id_col = pick("id", "case_id", "caseid")
    if id_col:
        mapping["id"] = id_col

    domain_col = pick("domain", "领域")
    if domain_col:
        mapping["domain"] = domain_col

    title_col = pick("title", "name", "标题")
    if title_col:
        mapping["title"] = title_col

    desc_col = pick("description", "desc", "描述")
    if desc_col:
        mapping["description"] = desc_col

    decision_node_col = pick("decision_node", "decision", "决策节点")
    if decision_node_col:
        mapping["decision_node"] = decision_node_col

    action_col = pick("action_taken", "action", "采取行动")
    if action_col:
        mapping["action_taken"] = action_col

    outcome_col = pick("outcome_result", "outcome", "结果")
    if outcome_col:
        mapping["outcome_result"] = outcome_col

    timeline_col = pick("outcome_timeline", "timeline", "历时", "时间线")
    if timeline_col:
        mapping["outcome_timeline"] = timeline_col

    lesson_col = pick("lesson_core", "lesson", "教训", "核心教训")
    if lesson_col:
        mapping["lesson_core"] = lesson_col

    confidence_col = pick("confidence", "置信度")
    if confidence_col:
        mapping["confidence"] = confidence_col

    return mapping


def _build_case_from_row(
    row: Dict[str, str],
    column_map: Dict[str, str],
    defaults: Dict[str, Any],
    *,
    allow_missing_id: bool = False,
    allow_missing_domain: bool = False,
    allow_missing_title: bool = False,
) -> Case:
    def get(field: str) -> str:
        col = column_map.get(field)
        if col and col in row:
            return (row.get(col) or "").strip()
        v = defaults.get(field, "")
        return str(v).strip() if v is not None else ""

    case_id = get("id")
    domain = get("domain")
    title = get("title")
    if not case_id:
        if allow_missing_id:
            raw = "\n".join(f"{k}:{(v or '').strip()}" for k, v in row.items() if (v or '').strip())
            case_id = f"case_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"
        else:
            raise ValueError("Missing required field: id")
    if not domain:
        if allow_missing_domain:
            domain = defaults.get("domain") or "general"
        else:
            raise ValueError(f"Missing required field: domain (case id: {case_id})")
    if not title:
        if allow_missing_title:
            title = case_id
        else:
            raise ValueError(f"Missing required field: title (case id: {case_id})")

    now = utc_now()
    return Case(
        id=case_id,
        domain=domain,
        title=title,
        description=get("description") or None,
        decision_node=get("decision_node") or None,
        action_taken=get("action_taken") or None,
        outcome_result=get("outcome_result") or None,
        outcome_timeline=get("outcome_timeline") or None,
        lesson_core=get("lesson_core") or None,
        confidence=get("confidence") or None,
        created_at=now,
        updated_at=now,
    )


def _row_to_text(row: Dict[str, str]) -> str:
    parts: list[str] = []
    for k, v in row.items():
        vv = (v or "").strip()
        if not vv:
            continue
        parts.append(f"{k}: {vv}")
    return "\n".join(parts)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _extract_text_from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Missing PDF dependency. Install with: pip install -e '.[ingest]'"
        ) from e

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
        raise RuntimeError(
            "Missing DOCX dependency. Install with: pip install -e '.[ingest]'"
        ) from e

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
        suf = path.suffix.lower().lstrip(".")
        resolved = suf

    if resolved == "pdf":
        text = _extract_text_from_pdf(path)
        _validate_extracted_document_text(text, path)
        return text
    if resolved == "docx":
        text = _extract_text_from_docx(path)
        _validate_extracted_document_text(text, path)
        return text

    raise RuntimeError(f"Unsupported document type: {doc_type}")


def _validate_extracted_document_text(text: str, path: Path) -> None:
    normalized = (text or "").strip()
    if not normalized:
        return

    suspicious_chars = sum(1 for ch in normalized if ch in {"?", "\ufffd"})
    dense_unknowns = "????" in normalized or "\ufffd\ufffd\ufffd\ufffd" in normalized
    suspicious_ratio = suspicious_chars / max(len(normalized), 1)

    if suspicious_chars >= 8 and (dense_unknowns or suspicious_ratio >= 0.2):
        raise RuntimeError(
            f"Extracted text from {path.name} looks corrupted. "
            "The source document may contain unsupported fonts/encoding or already-broken text."
        )


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


def _strip_html(text: str) -> str:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text or "")
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _import_csv_file(
    *,
    engine: Engine,
    csv_path: Path,
    mapping_path: str,
    default_domain: str,
    on_conflict: str,
    llm: str,
    api_base: str,
    llm_model: str,
    llm_mode: str,
    use_tabular: bool = False,
    allow_missing_id: bool = False,
    allow_missing_domain: bool = False,
    allow_missing_title: bool = False,
) -> tuple[int, int, int, list[str]]:
    try:
        mapping_data = _load_mapping(mapping_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load mapping: {e}")

    defaults: Dict[str, Any] = mapping_data.get("defaults", {}) if isinstance(mapping_data, dict) else {}
    if default_domain:
        defaults = dict(defaults)
        defaults["domain"] = default_domain

    imported = 0
    skipped = 0
    failed = 0
    case_ids: list[str] = []

    use_llm = llm == "api"
    if use_llm and not llm_model:
        raise RuntimeError("--llm-model is required when --llm api")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError("CSV has no header row.")

        rows = [row for row in reader]
        if use_tabular:
            rows = _normalize_rows_with_tabular(rows)

        headers = list(rows[0].keys()) if rows else list(reader.fieldnames)
        auto_map = _auto_column_map(headers)
        user_map = mapping_data.get("columns", {}) if isinstance(mapping_data, dict) else {}
        if user_map and not isinstance(user_map, dict):
            raise RuntimeError("mapping.columns must be a dict")

        column_map = dict(auto_map)
        for k, v in (user_map or {}).items():
            if isinstance(k, str) and isinstance(v, str) and v:
                column_map[k] = v

        for i, row in enumerate(rows, start=2):
            try:
                base_case = _build_case_from_row(
                    row,
                    column_map=column_map,
                    defaults=defaults,
                    allow_missing_id=allow_missing_id,
                    allow_missing_domain=allow_missing_domain,
                    allow_missing_title=allow_missing_title,
                )

                case = base_case
                if use_llm:
                    if llm_mode == "extract":
                        raw_text = _row_to_text(row)
                        llm_data = _api_extract_case(
                            api_base=api_base,
                            model=llm_model,
                            raw_text=raw_text,
                        )
                        case = _merge_llm_case_fields(base_case, llm_data)
                    else:
                        raw_text = _row_to_text(
                            {
                                "id": base_case.id,
                                "domain": base_case.domain,
                                "title": base_case.title,
                                "description": base_case.description or "",
                                "decision_node": base_case.decision_node or "",
                                "action_taken": base_case.action_taken or "",
                                "outcome_result": base_case.outcome_result or "",
                                "outcome_timeline": base_case.outcome_timeline or "",
                                "lesson_core": base_case.lesson_core or "",
                                "confidence": base_case.confidence or "",
                            }
                        )
                        llm_data = _api_extract_case(
                            api_base=api_base,
                            model=llm_model,
                            raw_text=raw_text,
                        )
                        case = _merge_llm_case_fields(base_case, llm_data)

                if on_conflict == "skip" and engine.db.case_exists(case.id):
                    skipped += 1
                    continue

                engine.add_case(case)
                imported += 1
                case_ids.append(case.id)
            except Exception as e:
                failed += 1
                log.error("%s row %s failed: %s", csv_path, i, e)

    return imported, skipped, failed, case_ids


def _import_json_file(
    *,
    engine: Engine,
    json_path: Path,
    mapping_path: str,
    default_domain: str,
    on_conflict: str,
    lock: threading.Lock,
    is_jsonl: bool = False,
    use_tabular: bool = False,
    allow_missing_id: bool = True,
    allow_missing_domain: bool = True,
    allow_missing_title: bool = True,
) -> tuple[int, int, int, list[str]]:
    try:
        mapping_data = _load_mapping(mapping_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load mapping: {e}")

    defaults: Dict[str, Any] = mapping_data.get("defaults", {}) if isinstance(mapping_data, dict) else {}
    if default_domain:
        defaults = dict(defaults)
        defaults["domain"] = default_domain

    raw_text = json_path.read_text(encoding="utf-8", errors="replace")
    payload: list[dict]
    if is_jsonl:
        payload = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                raise RuntimeError(f"Invalid JSONL line: {e}")
            if isinstance(obj, dict):
                payload.append(obj)
        if not payload:
            raise RuntimeError("JSONL file is empty")
    else:
        payload_raw = json.loads(raw_text)
        payload = _coerce_json_cases_payload(payload_raw)
        if not payload:
            raise RuntimeError("JSON must be an array of objects (or wrapped as {cases/items/data/rows: [...]})")

    rows = payload
    if use_tabular:
        rows = _normalize_rows_with_tabular(rows)

    headers: list[str] = []
    for obj in rows:
        if isinstance(obj, dict):
            headers.extend([str(k) for k in obj.keys()])
    headers = list(dict.fromkeys(headers))

    auto_map = _auto_column_map(headers)
    user_map = mapping_data.get("columns", {}) if isinstance(mapping_data, dict) else {}
    if user_map and not isinstance(user_map, dict):
        raise RuntimeError("mapping.columns must be a dict")

    column_map = dict(auto_map)
    for k, v in (user_map or {}).items():
        if isinstance(k, str) and isinstance(v, str) and v:
            column_map[k] = v

    imported = 0
    skipped = 0
    failed = 0
    case_ids: list[str] = []

    for idx, obj in enumerate(rows, start=1):
        try:
            row = {str(k): _normalize_ingest_value(v) for k, v in obj.items()}
            case = _build_case_from_row(
                row,
                column_map=column_map,
                defaults=defaults,
                allow_missing_id=allow_missing_id,
                allow_missing_domain=allow_missing_domain,
                allow_missing_title=allow_missing_title,
            )
            case_id = case.id
            with lock:
                if on_conflict == "skip" and engine.db.case_exists(case_id):
                    skipped += 1
                    continue
                engine.add_case(case)
            imported += 1
            case_ids.append(case_id)
        except Exception as e:
            failed += 1
            log.error("%s row %s failed: %s", json_path, idx, e)
    return imported, skipped, failed, case_ids


def _ingest_markdown_file(
    *,
    engine: Engine,
    md_path: Path,
    default_domain: str,
    on_conflict: str,
    lock: threading.Lock,
) -> tuple[int, int, int, list[str]]:
    raw = md_path.read_text(encoding="utf-8", errors="replace")
    note = _extract_markdown_note(raw)
    meta_raw = note.get("meta")
    meta: Dict[str, Any] = meta_raw if isinstance(meta_raw, dict) else {}
    title = str(note.get("title") or md_path.stem).strip() or md_path.stem
    domain = str(meta.get("domain") or default_domain or "general").strip() or "general"
    case_id = str(meta.get("id") or f"case_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}")

    now = utc_now()
    case = Case(
        id=case_id,
        domain=domain,
        title=title[:300],
        description=(note.get("body") or "")[:8000] or None,
        decision_node=str(meta.get("decision_node") or "") or None,
        action_taken=str(meta.get("action_taken") or "") or None,
        outcome_result=str(meta.get("outcome_result") or "") or None,
        outcome_timeline=str(meta.get("outcome_timeline") or "") or None,
        lesson_core=str(meta.get("lesson_core") or "") or None,
        confidence=str(meta.get("confidence") or "") or None,
        created_at=now,
        updated_at=now,
    )

    with lock:
        if on_conflict == "skip" and engine.db.case_exists(case.id):
            return 0, 1, 0, []
        engine.add_case(case)
    return 1, 0, 0, [case.id]


def _ingest_text_file(
    *,
    engine: Engine,
    file_path: Path,
    default_domain: str,
    on_conflict: str,
    lock: threading.Lock,
    is_html: bool = False,
) -> tuple[int, int, int, list[str]]:
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    text = _strip_html(raw) if is_html else raw.strip()
    if not text:
        raise RuntimeError("Empty text content")

    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    now = utc_now()
    case = Case(
        id=f"case_{sha[:16]}",
        domain=(default_domain or "general").strip() or "general",
        title=file_path.stem[:300],
        description=text[:8000],
        created_at=now,
        updated_at=now,
    )

    with lock:
        if on_conflict == "skip" and engine.db.case_exists(case.id):
            return 0, 1, 0, []
        engine.add_case(case)
    return 1, 0, 0, [case.id]


def _api_extract_case(
    *,
    api_base: str,
    model: str,
    raw_text: str,
) -> Dict[str, Any]:
    prompt = (
        "你是一位导入整理助手，负责把原始材料整理成 VintageWisdom 可入库的“决策案例”。\n"
        "目标不是泛泛摘要，而是提炼出一个可复用、可检索、可后续分析的案例对象。\n"
        "请只输出严格 JSON，不要输出任何额外说明、标题、代码块或注释。\n"
        "字段要求：\n"
        "- id: 字符串，必填。若原文没有明确 id，请生成一个稳定 id，只允许小写字母、数字、下划线，例如 case_20260315_001。\n"
        "- domain: 字符串，必填。优先根据材料推断；无法判断时使用 career。\n"
        "- title: 字符串，必填。要求简洁明确，像一个能被快速识别的案例标题。\n"
        "- description: 字符串，可为空。保留背景、约束和触发情境，不要写成空泛总结。\n"
        "- decision_node: 字符串，可为空。提炼“当时到底在权衡什么决策”。\n"
        "- action_taken: 字符串，可为空。写清采取了什么动作。\n"
        "- outcome_result: 字符串，可为空。写清结果，不要只写过程。\n"
        "- outcome_timeline: 字符串，可为空。写结果发生的大致时间窗，如“3个月”“1年内”。\n"
        "- lesson_core: 字符串，可为空。提炼最可迁移的一条教训。\n"
        "- confidence: 字符串，可为空。只能是 low、medium、high 之一。\n"
        "抽取原则：\n"
        "1. 优先保留与“决策、动作、结果、教训”最相关的信息。\n"
        "2. 如果材料更像事件记录，也要尽量转成“人在什么情境下做了什么判断”的案例视角。\n"
        "3. 不要臆造没有证据的细节；没有就留空。\n"
        "4. title、decision_node、lesson_core 要可读、可复用、适合后续检索。\n"
        "domain 建议取值：tech, business, career, political, life。\n"
        "confidence 建议取值：low, medium, high。\n\n"
        "原始文本：\n"
        f"{raw_text}\n"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一位严谨的中文信息抽取助手，只返回可解析的 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    final_api_base = (api_base or "").strip()
    if not final_api_base:
        raise RuntimeError("Missing --api-base for --llm api")
    api_key = ""
    try:
        from os import getenv
        api_key = getenv("AI_API_KEY", "") or ""
    except Exception:
        api_key = ""
    if not api_key:
        raise RuntimeError("Missing AI_API_KEY environment variable for --llm api")

    url = final_api_base.rstrip("/") + "/chat/completions"
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
    except Exception as e:
        raise RuntimeError(f"API request failed: {e}")

    data = json.loads(body)
    if data.get("error"):
        raise RuntimeError(f"API error: {data.get('error')}")

    choices = data.get("choices") if isinstance(data, dict) else None
    message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    response_text = (message.get("content") if isinstance(message, dict) else "") or ""
    response_text = response_text.strip()
    if not response_text:
        raise RuntimeError("API returned empty response")

    extracted = json.loads(response_text)
    if not isinstance(extracted, dict):
        raise RuntimeError("API response is not a JSON object")
    return extracted


def _merge_llm_case_fields(
    base: Case,
    llm_data: Dict[str, Any],
) -> Case:
    def pick(name: str) -> str | None:
        v = llm_data.get(name)
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s or None
        return str(v).strip() or None

    now = utc_now()
    return Case(
        id=pick("id") or base.id,
        domain=pick("domain") or base.domain,
        title=pick("title") or base.title,
        description=pick("description") or base.description,
        decision_node=pick("decision_node") or base.decision_node,
        action_taken=pick("action_taken") or base.action_taken,
        outcome_result=pick("outcome_result") or base.outcome_result,
        outcome_timeline=pick("outcome_timeline") or base.outcome_timeline,
        lesson_core=pick("lesson_core") or base.lesson_core,
        confidence=pick("confidence") or base.confidence,
        created_at=base.created_at,
        updated_at=now,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from .. import __version__

        print(__version__)
        return 0

    if not args.command:
        parser.print_help()
        return 1

    from ..core.app import VintageWisdomApp

    vw_app = VintageWisdomApp()
    vw_app.initialize()
    engine = vw_app.engine

    if args.command == "init":
        print("Initialized local storage.")
        return 0

    if args.command == "tui":
        from .app import run_tui

        run_tui()
        return 0

    if args.command == "query":
        query_text = " ".join(args.text)
        result = engine.query(query_text)
        print(f"Query: {query_text}")
        print(f"Matches: {len(result.cases)}")
        for case in result.cases:
            print(f"- {case.id}: {case.title}")
        print("Reasoning:")
        print(result.reasoning)
        if result.recommendations:
            print("Recommendations:")
            for item in result.recommendations:
                print(f"- {item}")
        return 0

    if args.command == "add-case":
        case = Case(
            id=args.id,
            domain=args.domain,
            title=args.title,
            description=args.description or None,
            decision_node=args.decision_node or None,
            action_taken=args.action_taken or None,
            outcome_result=args.outcome_result or None,
            outcome_timeline=args.outcome_timeline or None,
            lesson_core=args.lesson_core or None,
            confidence=args.confidence or None,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        engine.add_case(case)
        print(f"Added case {case.id}.")
        return 0

    if args.command == "log-decision":
        log_entry = DecisionLog(
            id=args.id,
            query=args.query,
            context={"text": args.context} if args.context else {},
            user_decision=args.choice or None,
            predicted_outcome=args.predict or None,
            created_at=utc_now(),
            evaluated_at=None,
        )
        engine.log_decision(log_entry)
        print(f"Logged decision {log_entry.id}.")
        return 0

    if args.command == "evaluate-decision":
        try:
            engine.evaluate_decision(decision_id=args.id, actual_outcome=args.outcome)
        except KeyError:
            print(f"Decision not found: {args.id}", file=sys.stderr)
            return 1
        print(f"Evaluated decision {args.id}.")
        return 0

    if args.command == "import-csv":
        csv_path = Path(args.file)
        if not csv_path.exists() or not csv_path.is_file():
            print(f"CSV file not found: {args.file}", file=sys.stderr)
            return 1

        try:
            mapping_data = _load_mapping(args.mapping)
        except Exception as e:
            print(f"Failed to load mapping: {e}", file=sys.stderr)
            return 1

        defaults: Dict[str, Any] = mapping_data.get("defaults", {}) if isinstance(mapping_data, dict) else {}
        if args.default_domain:
            defaults = dict(defaults)
            defaults["domain"] = args.default_domain

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print("CSV has no header row.", file=sys.stderr)
                return 1

            auto_map = _auto_column_map(list(reader.fieldnames))
            user_map = mapping_data.get("columns", {}) if isinstance(mapping_data, dict) else {}
            if user_map and not isinstance(user_map, dict):
                print("mapping.columns must be a dict", file=sys.stderr)
                return 1

            column_map = dict(auto_map)
            for k, v in (user_map or {}).items():
                if isinstance(k, str) and isinstance(v, str) and v:
                    column_map[k] = v

            imported = 0
            skipped = 0
            failed = 0

            use_llm = args.llm == "api"
            if use_llm and not args.llm_model:
                print("--llm-model is required when --llm api", file=sys.stderr)
                return 1

            for i, row in enumerate(reader, start=2):
                try:
                    base_case = _build_case_from_row(row, column_map=column_map, defaults=defaults)

                    case = base_case
                    if use_llm:
                        if args.llm_mode == "extract":
                            raw_text = _row_to_text(row)
                            llm_data = _api_extract_case(
                                api_base=args.api_base,
                                model=args.llm_model,
                                raw_text=raw_text,
                            )
                            case = _merge_llm_case_fields(base_case, llm_data)
                        else:
                            raw_text = _row_to_text({
                                "id": base_case.id,
                                "domain": base_case.domain,
                                "title": base_case.title,
                                "description": base_case.description or "",
                                "decision_node": base_case.decision_node or "",
                                "action_taken": base_case.action_taken or "",
                                "outcome_result": base_case.outcome_result or "",
                                "outcome_timeline": base_case.outcome_timeline or "",
                                "lesson_core": base_case.lesson_core or "",
                                "confidence": base_case.confidence or "",
                            })
                            llm_data = _api_extract_case(
                                api_base=args.api_base,
                                model=args.llm_model,
                                raw_text=raw_text,
                            )
                            case = _merge_llm_case_fields(base_case, llm_data)

                    if args.on_conflict == "skip" and engine.db.case_exists(case.id):
                        skipped += 1
                        continue
                    if not args.dry_run:
                        engine.add_case(case)
                    imported += 1
                except Exception as e:
                    failed += 1
                    print(f"Row {i} failed: {e}", file=sys.stderr)

        if args.dry_run:
            print(
                f"Dry-run complete. Would import: {imported}, skipped: {skipped}, failed: {failed}"
            )
        else:
            print(f"Import complete. Imported: {imported}, skipped: {skipped}, failed: {failed}")
        return 0

    if args.command == "scan-csv":
        scan_dir = Path(args.dir)
        if not scan_dir.exists() or not scan_dir.is_dir():
            print(f"Directory not found: {args.dir}", file=sys.stderr)
            return 1

        while True:
            files = sorted(scan_dir.glob(args.pattern))
            for csv_path in files:
                if not csv_path.is_file():
                    continue

                try:
                    sha = _sha256_file(csv_path)
                except Exception as e:
                    log.error("Failed to hash %s: %s", csv_path, e)
                    continue

                existing = engine.db.get_file_ingest_by_sha256(sha)
                if existing and existing.get("status") == "success":
                    continue

                ingest_id = f"csv_{sha}"
                mtime = None
                try:
                    mtime = csv_path.stat().st_mtime
                except Exception:
                    mtime = None

                engine.db.upsert_file_ingest(
                    ingest_id=ingest_id,
                    source_type="csv",
                    source_path=str(csv_path),
                    source_sha256=sha,
                    source_mtime=mtime,
                    status="running",
                    message=None,
                )
                try:
                    from ..core.events import events

                    events.emit("ingest.started", {"type": "csv", "sha256": sha, "filename": csv_path.name})
                except Exception:
                    pass

                try:
                    imported, skipped, failed, case_ids = _import_csv_file(
                        engine=engine,
                        csv_path=csv_path,
                        mapping_path=args.mapping,
                        default_domain=args.default_domain,
                        on_conflict=args.on_conflict,
                        llm=args.llm,
                        api_base=args.api_base,
                        llm_model=args.llm_model,
                        llm_mode=args.llm_mode,
                    )
                    status = "success" if failed == 0 else "partial"
                    engine.db.upsert_file_ingest(
                        ingest_id=ingest_id,
                        source_type="csv",
                        source_path=str(csv_path),
                        source_sha256=sha,
                        source_mtime=mtime,
                        status=status,
                        imported_count=imported,
                        skipped_count=skipped,
                        failed_count=failed,
                        message=None,
                    )
                    try:
                        from ..core.events import events

                        events.emit(
                            "ingest.completed",
                            {"type": "csv", "sha256": sha, "case_ids": case_ids, "status": status},
                        )
                    except Exception:
                        pass
                except Exception as e:
                    engine.db.upsert_file_ingest(
                        ingest_id=ingest_id,
                        source_type="csv",
                        source_path=str(csv_path),
                        source_sha256=sha,
                        source_mtime=mtime,
                        status="failed",
                        message=str(e),
                    )
                    log.error("Import failed for %s: %s", csv_path, e)
                    try:
                        from ..core.events import events

                        events.emit("ingest.failed", {"type": "csv", "sha256": sha, "error": str(e)})
                    except Exception:
                        pass

            if args.once:
                return 0
            time.sleep(max(0.5, float(args.interval)))

    if args.command == "ingest-dir":
        scan_dir = Path(args.dir)
        if not scan_dir.exists() or not scan_dir.is_dir():
            print(f"Directory not found: {args.dir}", file=sys.stderr)
            return 1

        from ..core.events import events

        pattern = args.pattern or "**/*"
        files = [p for p in scan_dir.glob(pattern) if p.is_file()]
        if not files:
            print("No files matched.")
            return 0

        lock = threading.Lock()

        def process_path(p: Path) -> Dict[str, Any]:
            ext = p.suffix.lower()
            kind = ""
            if ext == ".csv":
                kind = "csv"
            elif ext in {".json", ".jsonl"}:
                kind = "json"
            elif ext in {".md", ".markdown"}:
                kind = "markdown"
            elif ext in {".pdf", ".docx"}:
                kind = "document"
            elif ext in {".html", ".htm"}:
                kind = "html"
            elif ext == ".txt":
                kind = "text"
            else:
                return {"path": str(p), "status": "ignored", "reason": "unsupported"}

            try:
                sha = _sha256_file(p)
            except Exception as e:
                return {"path": str(p), "status": "failed", "error": str(e)}

            existing = engine.db.get_file_ingest_by_sha256(sha)
            if existing and existing.get("status") == "success":
                return {"path": str(p), "status": "skipped", "reason": "already ingested"}

            ingest_id = f"{kind}_{sha}"
            try:
                mtime = p.stat().st_mtime
            except Exception:
                mtime = None

            with lock:
                engine.db.upsert_file_ingest(
                    ingest_id=ingest_id,
                    source_type=kind,
                    source_path=str(p),
                    source_sha256=sha,
                    source_mtime=mtime,
                    status="running",
                    message=None,
                )
            try:
                events.emit("ingest.started", {"type": kind, "sha256": sha, "filename": p.name})
            except Exception:
                pass

            imported = skipped = failed = 0
            case_ids: list[str] = []
            try:
                if kind == "csv":
                    imported, skipped, failed, case_ids = _import_csv_file(
                        engine=engine,
                        csv_path=p,
                        mapping_path=args.mapping,
                        default_domain=args.default_domain,
                        on_conflict=args.on_conflict,
                        llm=args.llm,
                        api_base=args.api_base,
                        llm_model=args.llm_model,
                        llm_mode=args.llm_mode,
                        use_tabular=bool(args.tabular),
                        allow_missing_id=True,
                        allow_missing_domain=True,
                        allow_missing_title=True,
                    )
                elif kind == "json":
                    imported, skipped, failed, case_ids = _import_json_file(
                        engine=engine,
                        json_path=p,
                        mapping_path=args.mapping,
                        default_domain=args.default_domain,
                        on_conflict=args.on_conflict,
                        lock=lock,
                        is_jsonl=(p.suffix.lower() == ".jsonl"),
                        use_tabular=bool(args.tabular),
                    )
                elif kind == "markdown":
                    imported, skipped, failed, case_ids = _ingest_markdown_file(
                        engine=engine,
                        md_path=p,
                        default_domain=args.default_domain,
                        on_conflict=args.on_conflict,
                        lock=lock,
                    )
                elif kind == "document":
                    text = _extract_document_text(p, "auto")
                    if not text:
                        raise RuntimeError("No text extracted")
                    sha_local = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    now = utc_now()
                    case = Case(
                        id=f"case_{sha_local[:16]}",
                        domain=(args.default_domain or "general").strip() or "general",
                        title=p.stem[:300],
                        description=text[:8000],
                        created_at=now,
                        updated_at=now,
                    )
                    with lock:
                        if args.on_conflict == "skip" and engine.db.case_exists(case.id):
                            imported, skipped, failed = 0, 1, 0
                        else:
                            engine.add_case(case)
                            imported = 1
                    case_ids = [case.id] if imported else []
                elif kind == "html":
                    imported, skipped, failed, case_ids = _ingest_text_file(
                        engine=engine,
                        file_path=p,
                        default_domain=args.default_domain,
                        on_conflict=args.on_conflict,
                        lock=lock,
                        is_html=True,
                    )
                elif kind == "text":
                    imported, skipped, failed, case_ids = _ingest_text_file(
                        engine=engine,
                        file_path=p,
                        default_domain=args.default_domain,
                        on_conflict=args.on_conflict,
                        lock=lock,
                        is_html=False,
                    )

                status = "success" if failed == 0 else "partial"
                with lock:
                    engine.db.upsert_file_ingest(
                        ingest_id=ingest_id,
                        source_type=kind,
                        source_path=str(p),
                        source_sha256=sha,
                        source_mtime=mtime,
                        status=status,
                        imported_count=imported,
                        skipped_count=skipped,
                        failed_count=failed,
                        message=None,
                    )
                try:
                    events.emit(
                        "ingest.completed",
                        {"type": kind, "sha256": sha, "case_ids": case_ids, "status": status},
                    )
                except Exception:
                    pass
                return {
                    "path": str(p),
                    "status": status,
                    "imported": imported,
                    "skipped": skipped,
                    "failed": failed,
                }
            except Exception as e:
                with lock:
                    engine.db.upsert_file_ingest(
                        ingest_id=ingest_id,
                        source_type=kind,
                        source_path=str(p),
                        source_sha256=sha,
                        source_mtime=mtime,
                        status="failed",
                        imported_count=imported,
                        skipped_count=skipped,
                        failed_count=max(1, failed),
                        message=str(e),
                    )
                try:
                    events.emit("ingest.failed", {"type": kind, "sha256": sha, "error": str(e)})
                except Exception:
                    pass
                return {"path": str(p), "status": "failed", "error": str(e)}

        workers = max(1, int(args.workers or 1))
        summaries: list[Dict[str, Any]] = []
        if workers == 1:
            for p in files:
                summaries.append(process_path(p))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = [pool.submit(process_path, p) for p in files]
                for fut in as_completed(futs):
                    try:
                        summaries.append(fut.result())
                    except Exception as e:
                        summaries.append({"path": "", "status": "failed", "error": str(e)})

        counts = {"success": 0, "partial": 0, "failed": 0, "skipped": 0, "ignored": 0}
        for s in summaries:
            status = s.get("status")
            if status in counts:
                counts[status] += 1
        print(
            "Ingest-dir summary: "
            f"success={counts['success']} partial={counts['partial']} failed={counts['failed']} "
            f"skipped={counts['skipped']} ignored={counts['ignored']}"
        )
        return 0

    if args.command == "ingest-doc":
        doc_path = Path(args.file)
        if not doc_path.exists() or not doc_path.is_file():
            print(f"File not found: {args.file}", file=sys.stderr)
            return 1

        try:
            sha = _sha256_file(doc_path)
        except Exception as e:
            print(f"Failed to hash file: {e}", file=sys.stderr)
            return 1

        existing = engine.db.get_file_ingest_by_sha256(sha)
        if existing and existing.get("status") == "success":
            print("Already ingested (sha256 exists).")
            return 0

        ingest_id = f"doc_{sha}"
        mtime = None
        try:
            mtime = doc_path.stat().st_mtime
        except Exception:
            mtime = None

        engine.db.upsert_file_ingest(
            ingest_id=ingest_id,
            source_type="document",
            source_path=str(doc_path),
            source_sha256=sha,
            source_mtime=mtime,
            status="running",
            message=None,
        )

        try:
            text = _extract_document_text(doc_path, args.type)
            if not text:
                raise RuntimeError("No text extracted")

            use_llm = args.llm == "api"
            if use_llm and not args.llm_model:
                raise RuntimeError("--llm-model is required when --llm api")

            now = utc_now()
            if use_llm:
                llm_data = _api_extract_case(
                    api_base=args.api_base,
                    model=args.llm_model,
                    raw_text=text,
                )
                base = Case(
                    id=args.id.strip() or f"case_{sha[:16]}",
                    domain=args.domain.strip() or "career",
                    title=(args.title.strip() or doc_path.stem)[:300],
                    description=(text[:8000] if text else "") or None,
                    created_at=now,
                    updated_at=now,
                )
                case = _merge_llm_case_fields(base, llm_data)
            else:
                case = Case(
                    id=args.id.strip() or f"case_{sha[:16]}",
                    domain=args.domain.strip() or "career",
                    title=(args.title.strip() or doc_path.stem)[:300],
                    description=(text[:8000] if text else "") or None,
                    created_at=now,
                    updated_at=now,
                )

            if engine.db.case_exists(case.id):
                engine.db.upsert_file_ingest(
                    ingest_id=ingest_id,
                    source_type="document",
                    source_path=str(doc_path),
                    source_sha256=sha,
                    source_mtime=mtime,
                    status="skipped",
                    imported_count=0,
                    skipped_count=1,
                    failed_count=0,
                    message=f"Case id already exists: {case.id}",
                )
                print(f"Skipped: case id already exists: {case.id}")
                return 0

            engine.add_case(case)
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="document",
                source_path=str(doc_path),
                source_sha256=sha,
                source_mtime=mtime,
                status="success",
                imported_count=1,
                skipped_count=0,
                failed_count=0,
                message=None,
            )
            print(f"Ingested document into case: {case.id}")
            return 0
        except Exception as e:
            engine.db.upsert_file_ingest(
                ingest_id=ingest_id,
                source_type="document",
                source_path=str(doc_path),
                source_sha256=sha,
                source_mtime=mtime,
                status="failed",
                imported_count=0,
                skipped_count=0,
                failed_count=1,
                message=str(e),
            )
            print(f"Ingest failed: {e}", file=sys.stderr)
            return 1

    if args.command == "stats":
        count = engine.db.count_cases()
        decisions = engine.db.count_decision_logs()
        evaluated = engine.db.count_evaluated_decision_logs()
        print(f"Cases: {count}")
        print(f"DecisionLogs: {decisions} (evaluated: {evaluated})")
        return 0

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
