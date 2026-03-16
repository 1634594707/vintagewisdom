"""
异步任务存储 - 用于跟踪导入任务的进度
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock


class TaskStore:
    """任务存储管理"""
    
    def __init__(self, db_path: Path):
        self.path = Path(db_path)
        self._lock = Lock()
        self._init_db()
    
    def _init_db(self):
        """初始化任务表"""
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS import_tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,  -- pending, processing, completed, failed
                total_cases INTEGER DEFAULT 0,
                processed_cases INTEGER DEFAULT 0,
                stage TEXT DEFAULT 'import',
                stage_done INTEGER DEFAULT 0,
                stage_total INTEGER DEFAULT 0,
                current_case TEXT,
                current_action TEXT,
                result TEXT,  -- JSON
                error_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Lightweight migration for existing DBs (SQLite has no IF NOT EXISTS for columns)
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(import_tasks)").fetchall()]
            if "stage" not in cols:
                conn.execute("ALTER TABLE import_tasks ADD COLUMN stage TEXT DEFAULT 'import'")
            if "stage_done" not in cols:
                conn.execute("ALTER TABLE import_tasks ADD COLUMN stage_done INTEGER DEFAULT 0")
            if "stage_total" not in cols:
                conn.execute("ALTER TABLE import_tasks ADD COLUMN stage_total INTEGER DEFAULT 0")
        except Exception:
            pass

        conn.commit()
        conn.close()
    
    def create_task(self, task_id: str, total_cases: int = 0) -> None:
        """创建新任务"""
        with self._lock:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            now = datetime.utcnow().isoformat()
            conn.execute(
                """INSERT INTO import_tasks 
                   (task_id, status, total_cases, processed_cases, stage, stage_done, stage_total, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, "pending", total_cases, 0, "import", 0, total_cases, now, now)
            )
            conn.commit()
            conn.close()

    def update_stage(self, task_id: str, stage: str, done: int = 0, total: int = 0, current_action: str = "") -> None:
        """更新任务阶段与阶段进度（不影响 processed_cases/total_cases）。"""
        with self._lock:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            now = datetime.utcnow().isoformat()
            conn.execute(
                """UPDATE import_tasks
                   SET stage = ?,
                       stage_done = ?,
                       stage_total = ?,
                       current_action = COALESCE(NULLIF(?, ''), current_action),
                       updated_at = ?
                   WHERE task_id = ?""",
                (stage, int(done or 0), int(total or 0), current_action, now, task_id),
            )
            conn.commit()
            conn.close()
    
    def update_progress(
        self, 
        task_id: str, 
        processed: int, 
        current_case: str = "",
        current_action: str = ""
    ) -> None:
        """更新任务进度"""
        with self._lock:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            now = datetime.utcnow().isoformat()
            conn.execute(
                """UPDATE import_tasks 
                   SET processed_cases = ?, 
                       current_case = ?,
                       current_action = ?,
                       updated_at = ?
                   WHERE task_id = ?""",
                (processed, current_case, current_action, now, task_id)
            )
            conn.commit()
            conn.close()
    
    def update_status(
        self, 
        task_id: str, 
        status: str, 
        result: Optional[Dict] = None,
        error_message: str = ""
    ) -> None:
        """更新任务状态"""
        with self._lock:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            now = datetime.utcnow().isoformat()
            result_json = json.dumps(result, ensure_ascii=False) if result else None
            conn.execute(
                """UPDATE import_tasks 
                   SET status = ?, 
                       result = ?,
                       error_message = ?,
                       updated_at = ?
                   WHERE task_id = ?""",
                (status, result_json, error_message, now, task_id)
            )
            conn.commit()
            conn.close()
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM import_tasks WHERE task_id = ?",
            (task_id,)
        ).fetchone()
        conn.close()
        
        if not row:
            return None
        
        result = dict(row)
        if result.get('result'):
            try:
                result['result'] = json.loads(result['result'])
            except:
                pass
        return result
    
    def cleanup_old_tasks(self, hours: int = 24) -> int:
        """清理旧任务"""
        with self._lock:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            cursor = conn.execute(
                "DELETE FROM import_tasks WHERE updated_at < datetime('now', '-{} hours')".format(hours)
            )
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted


# 全局任务存储实例
_task_store: Optional[TaskStore] = None


def get_task_store(db_path: Optional[Path] = None) -> TaskStore:
    """获取任务存储实例"""
    global _task_store
    if _task_store is None:
        if db_path is None:
            db_path = Path("data/vintagewisdom.db")
        _task_store = TaskStore(db_path)
    return _task_store
