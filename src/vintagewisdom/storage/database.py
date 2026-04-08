from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.case import Case
from ..models.decision import DecisionLog
from ..utils.helpers import utc_now, utc_now_iso


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
                tags TEXT,
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
            if "tags" not in cols:
                conn.execute("ALTER TABLE cases ADD COLUMN tags TEXT")
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
        
        # 案例版本历史表
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(case_id, version_number)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_case_versions_case_id ON case_versions (case_id);
            """
        )
        
        # 标签表
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            """
        )
        
        # 案例标签关联表
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS case_tags (
                case_id TEXT NOT NULL,
                tag_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (case_id, tag_id)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_case_tags_tag_id ON case_tags (tag_id);
            """
        )
        
        # 异步任务表
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS async_tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                total_cases INTEGER NOT NULL,
                processed_cases INTEGER NOT NULL,
                stage TEXT,
                stage_done INTEGER,
                stage_total INTEGER,
                current_case TEXT,
                current_action TEXT,
                result TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
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
        ts = (extracted_at or utc_now()).isoformat()
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
        now = utc_now()
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
        now = utc_now()
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
        ts = (created_at or utc_now()).isoformat()
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
        now = utc_now()
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
        ts = (evaluated_at or utc_now()).isoformat()
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
        now = utc_now()
        created_at = case.created_at or now
        updated_at = case.updated_at or now
        
        # 序列化tags为JSON
        tags_json = json.dumps(case.tags or [], ensure_ascii=False) if case.tags else None
        
        conn.execute(
            """
            INSERT OR REPLACE INTO cases (
                id, domain, title, description, decision_node, action_taken,
                outcome_result, outcome_timeline, lesson_core, confidence,
                domain_tags, tags,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                tags_json,
                created_at.isoformat(),
                updated_at.isoformat(),
            ),
        )
        conn.commit()

        events.emit("db.case.inserted", {"case": case})

    def list_cases(self) -> List[Case]:
        conn = self.connect()
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        cases = []
        for row in rows:
            data = dict(row)
            # 反序列化tags
            if data.get("tags"):
                try:
                    data["tags"] = json.loads(data["tags"])
                except Exception:
                    data["tags"] = []
            cases.append(Case(**data))
        return cases

    def get_case(self, case_id: str) -> Case:
        conn = self.connect()
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            raise KeyError(case_id)
        data = dict(row)
        # 反序列化tags
        if data.get("tags"):
            try:
                data["tags"] = json.loads(data["tags"])
            except Exception:
                data["tags"] = []
        return Case(**data)

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

    # ========== 标签管理 ==========
    
    def create_tag(self, tag_name: str) -> str:
        """创建新标签"""
        import uuid
        conn = self.connect()
        tag_id = f"tag_{uuid.uuid4().hex[:8]}"
        now = utc_now_iso()
        try:
            conn.execute(
                "INSERT INTO tags (id, name, created_at) VALUES (?, ?, ?)",
                (tag_id, tag_name, now)
            )
            conn.commit()
            return tag_id
        except sqlite3.IntegrityError:
            # 标签已存在，返回现有ID
            row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            return row["id"] if row else tag_id
    
    def list_tags(self) -> List[Dict[str, Any]]:
        """列出所有标签及其使用次数"""
        conn = self.connect()
        rows = conn.execute("""
            SELECT t.id, t.name, t.created_at, COUNT(ct.case_id) as case_count
            FROM tags t
            LEFT JOIN case_tags ct ON t.id = ct.tag_id
            GROUP BY t.id, t.name, t.created_at
            ORDER BY case_count DESC, t.name ASC
        """).fetchall()
        return [dict(row) for row in rows]
    
    def delete_tag(self, tag_id: str) -> None:
        """删除标签及其所有关联"""
        conn = self.connect()
        conn.execute("DELETE FROM case_tags WHERE tag_id = ?", (tag_id,))
        conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
    
    def rename_tag(self, tag_id: str, new_name: str) -> None:
        """重命名标签"""
        conn = self.connect()
        conn.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name, tag_id))
        conn.commit()
    
    def add_case_tag(self, case_id: str, tag_id: str) -> None:
        """为案例添加标签"""
        conn = self.connect()
        now = utc_now_iso()
        try:
            conn.execute(
                "INSERT INTO case_tags (case_id, tag_id, created_at) VALUES (?, ?, ?)",
                (case_id, tag_id, now)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # 关联已存在
    
    def remove_case_tag(self, case_id: str, tag_id: str) -> None:
        """从案例移除标签"""
        conn = self.connect()
        conn.execute("DELETE FROM case_tags WHERE case_id = ? AND tag_id = ?", (case_id, tag_id))
        conn.commit()
    
    def get_case_tags(self, case_id: str) -> List[Dict[str, Any]]:
        """获取案例的所有标签"""
        conn = self.connect()
        rows = conn.execute("""
            SELECT t.id, t.name, t.created_at
            FROM tags t
            JOIN case_tags ct ON t.id = ct.tag_id
            WHERE ct.case_id = ?
            ORDER BY t.name ASC
        """, (case_id,)).fetchall()
        return [dict(row) for row in rows]
    
    # ========== 案例版本历史 ==========
    
    def save_case_version(self, case: Case) -> None:
        """保存案例版本"""
        conn = self.connect()
        # 获取当前最大版本号
        row = conn.execute(
            "SELECT MAX(version_number) as max_ver FROM case_versions WHERE case_id = ?",
            (case.id,)
        ).fetchone()
        next_version = (row["max_ver"] or 0) + 1
        
        # 保存版本（只保留最近10个版本）
        now = utc_now_iso()
        case_dict = case.model_dump()
        # 转换datetime为字符串
        for key, value in case_dict.items():
            if isinstance(value, datetime):
                case_dict[key] = value.isoformat()
        
        conn.execute(
            "INSERT INTO case_versions (case_id, version_number, data, created_at) VALUES (?, ?, ?, ?)",
            (case.id, next_version, json.dumps(case_dict, ensure_ascii=False), now)
        )
        
        # 删除旧版本（保留最近10个）
        conn.execute("""
            DELETE FROM case_versions 
            WHERE case_id = ? AND version_number NOT IN (
                SELECT version_number FROM case_versions 
                WHERE case_id = ? 
                ORDER BY version_number DESC 
                LIMIT 10
            )
        """, (case.id, case.id))
        conn.commit()
    
    def get_case_versions(self, case_id: str) -> List[Dict[str, Any]]:
        """获取案例的版本历史"""
        conn = self.connect()
        rows = conn.execute("""
            SELECT id, case_id, version_number, created_at
            FROM case_versions
            WHERE case_id = ?
            ORDER BY version_number DESC
        """, (case_id,)).fetchall()
        return [dict(row) for row in rows]
    
    def get_case_version(self, case_id: str, version_number: int) -> Optional[Case]:
        """获取特定版本的案例"""
        conn = self.connect()
        row = conn.execute(
            "SELECT data FROM case_versions WHERE case_id = ? AND version_number = ?",
            (case_id, version_number)
        ).fetchone()
        if not row:
            return None
        data = json.loads(row["data"])
        return Case(**data)
    
    # ========== 案例更新（带版本控制） ==========
    
    def update_case(self, case: Case) -> None:
        """更新案例并保存版本"""
        # 先保存当前版本
        try:
            old_case = self.get_case(case.id)
            self.save_case_version(old_case)
        except KeyError:
            pass  # 新案例，无需保存版本
        
        # 更新案例
        case.updated_at = utc_now()
        self.insert_case(case)
    
    # ========== 批量操作 ==========
    
    def delete_cases(self, case_ids: List[str]) -> int:
        """批量删除案例"""
        if not case_ids:
            return 0
        conn = self.connect()
        placeholders = ",".join(["?"] * len(case_ids))
        
        # 删除相关数据
        conn.execute(f"DELETE FROM case_tags WHERE case_id IN ({placeholders})", case_ids)
        conn.execute(f"DELETE FROM case_versions WHERE case_id IN ({placeholders})", case_ids)
        conn.execute(f"DELETE FROM kg_case_state WHERE case_id IN ({placeholders})", case_ids)
        conn.execute(f"DELETE FROM relation_evidence WHERE case_id IN ({placeholders})", case_ids)
        
        # 删除案例
        cursor = conn.execute(f"DELETE FROM cases WHERE id IN ({placeholders})", case_ids)
        deleted = cursor.rowcount
        conn.commit()
        return deleted
    
    def batch_add_tags(self, case_ids: List[str], tag_ids: List[str]) -> int:
        """批量添加标签"""
        if not case_ids or not tag_ids:
            return 0
        conn = self.connect()
        now = utc_now_iso()
        added = 0
        for case_id in case_ids:
            for tag_id in tag_ids:
                try:
                    conn.execute(
                        "INSERT INTO case_tags (case_id, tag_id, created_at) VALUES (?, ?, ?)",
                        (case_id, tag_id, now)
                    )
                    added += 1
                except sqlite3.IntegrityError:
                    pass  # 关联已存在
        conn.commit()
        return added
    
    def batch_remove_tags(self, case_ids: List[str], tag_ids: List[str]) -> int:
        """批量移除标签"""
        if not case_ids or not tag_ids:
            return 0
        conn = self.connect()
        case_placeholders = ",".join(["?"] * len(case_ids))
        tag_placeholders = ",".join(["?"] * len(tag_ids))
        cursor = conn.execute(
            f"DELETE FROM case_tags WHERE case_id IN ({case_placeholders}) AND tag_id IN ({tag_placeholders})",
            (*case_ids, *tag_ids)
        )
        removed = cursor.rowcount
        conn.commit()
        return removed
    
    # ========== 决策历史管理 ==========
    
    def list_decision_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出决策历史"""
        conn = self.connect()
        rows = conn.execute("""
            SELECT id, query, context, recommended_cases, user_decision, 
                   predicted_outcome, actual_outcome, created_at, evaluated_at
            FROM decision_logs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["context"] = json.loads(d.get("context") or "{}")
                d["recommended_cases"] = json.loads(d.get("recommended_cases") or "[]")
            except Exception:
                d["context"] = {}
                d["recommended_cases"] = []
            result.append(d)
        return result
    
    def get_decision_log(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """获取单个决策记录"""
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM decision_logs WHERE id = ?",
            (decision_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["context"] = json.loads(d.get("context") or "{}")
            d["recommended_cases"] = json.loads(d.get("recommended_cases") or "[]")
        except Exception:
            d["context"] = {}
            d["recommended_cases"] = []
        return d
    
    def delete_decision_log(self, decision_id: str) -> None:
        """删除决策记录"""
        conn = self.connect()
        conn.execute("DELETE FROM decision_logs WHERE id = ?", (decision_id,))
        conn.commit()
    
    def search_decision_logs(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """搜索决策历史"""
        conn = self.connect()
        qq = f"%{query}%"
        rows = conn.execute("""
            SELECT id, query, context, recommended_cases, user_decision,
                   predicted_outcome, actual_outcome, created_at, evaluated_at
            FROM decision_logs
            WHERE query LIKE ? OR user_decision LIKE ? OR predicted_outcome LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (qq, qq, qq, limit)).fetchall()
        
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["context"] = json.loads(d.get("context") or "{}")
                d["recommended_cases"] = json.loads(d.get("recommended_cases") or "[]")
            except Exception:
                d["context"] = {}
                d["recommended_cases"] = []
            result.append(d)
        return result
    
    # ========== 异步任务管理 ==========
    
    def create_async_task(self, task_id: str, total_cases: int) -> None:
        """创建异步任务"""
        conn = self.connect()
        now = utc_now_iso()
        conn.execute("""
            INSERT INTO async_tasks (
                task_id, status, total_cases, processed_cases, 
                stage, stage_done, stage_total, current_case, current_action,
                result, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, "pending", total_cases, 0, None, None, None, None, None, None, None, now, now))
        conn.commit()
    
    def update_async_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        processed_cases: Optional[int] = None,
        stage: Optional[str] = None,
        stage_done: Optional[int] = None,
        stage_total: Optional[int] = None,
        current_case: Optional[str] = None,
        current_action: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """更新异步任务状态"""
        conn = self.connect()
        now = utc_now_iso()
        
        updates = ["updated_at = ?"]
        params = [now]
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if processed_cases is not None:
            updates.append("processed_cases = ?")
            params.append(processed_cases)
        if stage is not None:
            updates.append("stage = ?")
            params.append(stage)
        if stage_done is not None:
            updates.append("stage_done = ?")
            params.append(stage_done)
        if stage_total is not None:
            updates.append("stage_total = ?")
            params.append(stage_total)
        if current_case is not None:
            updates.append("current_case = ?")
            params.append(current_case)
        if current_action is not None:
            updates.append("current_action = ?")
            params.append(current_action)
        if result is not None:
            updates.append("result = ?")
            params.append(json.dumps(result, ensure_ascii=False))
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        
        params.append(task_id)
        conn.execute(
            f"UPDATE async_tasks SET {', '.join(updates)} WHERE task_id = ?",
            params
        )
        conn.commit()
    
    def get_async_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取异步任务状态"""
        conn = self.connect()
        row = conn.execute("SELECT * FROM async_tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("result"):
            try:
                d["result"] = json.loads(d["result"])
            except Exception:
                d["result"] = None
        return d
