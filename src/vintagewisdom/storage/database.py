from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.case import Case
from ..models.decision import DecisionLog


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def initialize(self) -> None:
        conn = self.connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                decision_node TEXT,
                action_taken TEXT,
                outcome_result TEXT,
                outcome_timeline TEXT,
                lesson_core TEXT,
                confidence TEXT,
                domain_tags TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )

        # Lightweight migration for existing DBs
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()]
            if "domain_tags" not in cols:
                conn.execute("ALTER TABLE cases ADD COLUMN domain_tags TEXT")
        except Exception:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                attributes TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_entities_name ON entities (name);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (type);
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                source_entity_id TEXT NOT NULL,
                target_entity_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL,
                attributes TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relations_source ON relations (source_entity_id);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relations_target ON relations (target_entity_id);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relations_type ON relations (relation_type);
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS relation_evidence (
                id TEXT PRIMARY KEY,
                relation_id TEXT NOT NULL,
                case_id TEXT NOT NULL,
                quote TEXT NOT NULL,
                start_offset INTEGER,
                end_offset INTEGER,
                created_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relation_evidence_relation ON relation_evidence (relation_id);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relation_evidence_case ON relation_evidence (case_id);
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kg_case_state (
                case_id TEXT PRIMARY KEY,
                text_sha1 TEXT NOT NULL,
                extracted_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_kg_case_state_sha1 ON kg_case_state (text_sha1);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS file_ingests (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_sha256 TEXT NOT NULL,
                source_mtime REAL,
                status TEXT NOT NULL,
                imported_count INTEGER,
                skipped_count INTEGER,
                failed_count INTEGER,
                message TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_file_ingests_sha
            ON file_ingests (source_sha256);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_file_ingests_path
            ON file_ingests (source_path);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_logs (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                context TEXT,
                recommended_cases TEXT,
                user_decision TEXT,
                predicted_outcome TEXT,
                actual_outcome TEXT,
                created_at TEXT,
                evaluated_at TEXT
            );
            """
        )
        conn.commit()

    def get_kg_case_state(self, case_id: str) -> Optional[Dict[str, Any]]:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM kg_case_state WHERE case_id = ? LIMIT 1",
            (case_id,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_kg_case_state(self, *, case_id: str, text_sha1: str, extracted_at: Optional[datetime] = None) -> None:
        conn = self.connect()
        ts = (extracted_at or datetime.utcnow()).isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO kg_case_state (case_id, text_sha1, extracted_at)
            VALUES (?, ?, ?)
            """,
            (case_id, text_sha1, ts),
        )
        conn.commit()

    def upsert_entity(
        self,
        *,
        entity_id: str,
        name: str,
        entity_type: str,
        attributes: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        conn = self.connect()
        now = datetime.utcnow()
        created_ts = (created_at or now).isoformat()
        updated_ts = (updated_at or now).isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO entities (
                id, name, type, attributes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                name,
                entity_type,
                json.dumps(attributes or {}, ensure_ascii=False),
                created_ts,
                updated_ts,
            ),
        )
        conn.commit()

    def upsert_relation(
        self,
        *,
        relation_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relation_type: str,
        confidence: float = 0.5,
        attributes: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        conn = self.connect()
        now = datetime.utcnow()
        created_ts = (created_at or now).isoformat()
        updated_ts = (updated_at or now).isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO relations (
                id, source_entity_id, target_entity_id, relation_type,
                confidence, attributes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                relation_id,
                source_entity_id,
                target_entity_id,
                relation_type,
                float(confidence),
                json.dumps(attributes or {}, ensure_ascii=False),
                created_ts,
                updated_ts,
            ),
        )
        conn.commit()

    def add_relation_evidence(
        self,
        *,
        evidence_id: str,
        relation_id: str,
        case_id: str,
        quote: str,
        start_offset: int | None = None,
        end_offset: int | None = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        conn = self.connect()
        ts = (created_at or datetime.utcnow()).isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO relation_evidence (
                id, relation_id, case_id, quote, start_offset, end_offset, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (evidence_id, relation_id, case_id, quote, start_offset, end_offset, ts),
        )
        conn.commit()

    def search_entities(self, q: str, limit: int = 200) -> List[Dict[str, Any]]:
        conn = self.connect()
        qq = f"%{q}%"
        rows = conn.execute(
            "SELECT * FROM entities WHERE name LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (qq, int(limit)),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["attributes"] = json.loads(d.get("attributes") or "{}")
            except Exception:
                d["attributes"] = {}
            out.append(d)
        return out

    def get_entities_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        if not ids:
            return []
        conn = self.connect()
        placeholders = ",".join(["?"] * len(ids))
        rows = conn.execute(
            f"SELECT * FROM entities WHERE id IN ({placeholders})",
            (*ids,),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["attributes"] = json.loads(d.get("attributes") or "{}")
            except Exception:
                d["attributes"] = {}
            out.append(d)
        return out

    def list_entities(self, limit: int = 200) -> List[Dict[str, Any]]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT * FROM entities ORDER BY updated_at DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["attributes"] = json.loads(d.get("attributes") or "{}")
            except Exception:
                d["attributes"] = {}
            out.append(d)
        return out

    def list_relations_for_entities(self, entity_ids: List[str], limit: int = 1000) -> List[Dict[str, Any]]:
        if not entity_ids:
            return []
        conn = self.connect()
        placeholders = ",".join(["?"] * len(entity_ids))
        rows = conn.execute(
            f"""
            SELECT * FROM relations
            WHERE source_entity_id IN ({placeholders}) OR target_entity_id IN ({placeholders})
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (*entity_ids, *entity_ids, int(limit)),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["attributes"] = json.loads(d.get("attributes") or "{}")
            except Exception:
                d["attributes"] = {}
            out.append(d)
        return out

    def list_relation_evidence(self, relation_ids: List[str], limit: int = 2000) -> List[Dict[str, Any]]:
        if not relation_ids:
            return []
        conn = self.connect()
        placeholders = ",".join(["?"] * len(relation_ids))
        rows = conn.execute(
            f"SELECT * FROM relation_evidence WHERE relation_id IN ({placeholders}) ORDER BY created_at DESC LIMIT ?",
            (*relation_ids, int(limit)),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_file_ingest_by_sha256(self, sha256: str) -> dict | None:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM file_ingests WHERE source_sha256 = ? ORDER BY updated_at DESC LIMIT 1",
            (sha256,),
        ).fetchone()
        return dict(row) if row else None

    def get_file_ingest_by_path(self, path: str) -> dict | None:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM file_ingests WHERE source_path = ? ORDER BY updated_at DESC LIMIT 1",
            (path,),
        ).fetchone()
        return dict(row) if row else None

    def upsert_file_ingest(
        self,
        *,
        ingest_id: str,
        source_type: str,
        source_path: str,
        source_sha256: str,
        source_mtime: float | None,
        status: str,
        imported_count: int | None = None,
        skipped_count: int | None = None,
        failed_count: int | None = None,
        message: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        conn = self.connect()
        now = datetime.utcnow()
        created_ts = (created_at or now).isoformat()
        updated_ts = (updated_at or now).isoformat()
        conn.execute(
            """
            INSERT OR REPLACE INTO file_ingests (
                id, source_type, source_path, source_sha256, source_mtime, status,
                imported_count, skipped_count, failed_count, message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ingest_id,
                source_type,
                source_path,
                source_sha256,
                source_mtime,
                status,
                imported_count,
                skipped_count,
                failed_count,
                message,
                created_ts,
                updated_ts,
            ),
        )
        conn.commit()

    def insert_decision_log(self, log: DecisionLog) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT OR REPLACE INTO decision_logs (
                id, query, context, recommended_cases, user_decision,
                predicted_outcome, actual_outcome, created_at, evaluated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.id,
                log.query,
                json.dumps(log.context, ensure_ascii=False),
                json.dumps(log.recommended_cases, ensure_ascii=False),
                log.user_decision,
                log.predicted_outcome,
                log.actual_outcome,
                log.created_at.isoformat(),
                log.evaluated_at.isoformat() if log.evaluated_at else None,
            ),
        )
        conn.commit()

    def evaluate_decision_log(
        self,
        decision_id: str,
        actual_outcome: str,
        evaluated_at: datetime | None = None,
    ) -> None:
        conn = self.connect()
        ts = (evaluated_at or datetime.utcnow()).isoformat()
        cur = conn.execute(
            """
            UPDATE decision_logs
            SET actual_outcome = ?, evaluated_at = ?
            WHERE id = ?
            """,
            (actual_outcome, ts, decision_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise KeyError(decision_id)

    def insert_case(self, case: Case) -> None:
        from ..core.events import events

        conn = self.connect()
        now = datetime.utcnow()
        created_at = case.created_at or now
        updated_at = case.updated_at or now
        conn.execute(
            """
            INSERT OR REPLACE INTO cases (
                id, domain, title, description, decision_node, action_taken,
                outcome_result, outcome_timeline, lesson_core, confidence,
                domain_tags,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case.id,
                case.domain,
                case.title,
                case.description,
                case.decision_node,
                case.action_taken,
                case.outcome_result,
                case.outcome_timeline,
                case.lesson_core,
                case.confidence,
                case.domain_tags,
                created_at.isoformat(),
                updated_at.isoformat(),
            ),
        )
        conn.commit()

        events.emit("db.case.inserted", {"case": case})

    def list_cases(self) -> List[Case]:
        conn = self.connect()
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        return [Case(**dict(row)) for row in rows]

    def get_case(self, case_id: str) -> Case:
        conn = self.connect()
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            raise KeyError(case_id)
        return Case(**dict(row))

    def case_exists(self, case_id: str) -> bool:
        conn = self.connect()
        row = conn.execute("SELECT 1 AS ok FROM cases WHERE id = ? LIMIT 1", (case_id,)).fetchone()
        return row is not None

    def count_cases(self) -> int:
        conn = self.connect()
        row = conn.execute("SELECT COUNT(1) AS cnt FROM cases").fetchone()
        return int(row["cnt"]) if row else 0

    def count_decision_logs(self) -> int:
        conn = self.connect()
        row = conn.execute("SELECT COUNT(1) AS cnt FROM decision_logs").fetchone()
        return int(row["cnt"]) if row else 0

    def count_evaluated_decision_logs(self) -> int:
        conn = self.connect()
        row = conn.execute(
            "SELECT COUNT(1) AS cnt FROM decision_logs WHERE evaluated_at IS NOT NULL"
        ).fetchone()
        return int(row["cnt"]) if row else 0

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
