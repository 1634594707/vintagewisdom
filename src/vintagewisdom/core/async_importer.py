"""
异步导入处理器 - 支持后台 AI 分析和进度跟踪
"""

import threading
import json
import hashlib
from typing import Dict, List, Optional, Callable
from pathlib import Path

from ..utils.config import Config
from ..utils.helpers import utc_now

from ..storage.task_store import get_task_store
from ..storage.database import Database
from ..models.case import Case


class AsyncImporter:
    """异步导入处理器"""
    
    def __init__(self, db_path: Path):
        self.db = Database(db_path)
        self.db.initialize()
        self.task_store = get_task_store(db_path)
        self._active_tasks: Dict[str, threading.Thread] = {}
        self.config = Config()
    
    def start_import(
        self,
        task_id: str,
        cases_data: List[Dict],
        enable_ai_classify: bool = False,
        enable_ai_clustering: bool = False,
        default_domain: str = "",
        on_progress: Optional[Callable] = None
    ) -> str:
        """
        启动异步导入任务
        
        Returns:
            task_id: 任务ID，用于查询进度
        """
        # 创建任务记录
        self.task_store.create_task(task_id, total_cases=len(cases_data))
        
        # 启动后台线程
        thread = threading.Thread(
            target=self._import_worker,
            args=(
                task_id, 
                cases_data, 
                enable_ai_classify,
                enable_ai_clustering,
                default_domain
            ),
            daemon=True
        )
        self._active_tasks[task_id] = thread
        thread.start()
        
        return task_id
    
    def _import_worker(
        self,
        task_id: str,
        cases_data: List[Dict],
        enable_ai_classify: bool,
        enable_ai_clustering: bool,
        default_domain: str
    ):
        """导入工作线程"""
        try:
            self.task_store.update_status(task_id, "processing")
            
            imported = 0
            failed = 0
            skipped = 0
            case_ids: List[str] = []
            total_cases = len(cases_data)

            try:
                self.task_store.update_stage(task_id, "import", 0, total_cases, current_action="正在导入...")
            except Exception:
                pass
            
            # 1. 基础导入（不等待 AI）
            for i, case_data in enumerate(cases_data):
                try:
                    self.task_store.update_progress(
                        task_id, 
                        i + 1, 
                        current_case=case_data.get('title', 'Unknown')[:30],
                        current_action="正在导入..."
                    )

                    try:
                        self.task_store.update_stage(task_id, "import", i + 1, total_cases)
                    except Exception:
                        pass
                    
                    # 构建案例
                    case = self._build_case(case_data, default_domain)
                    
                    # 检查是否已存在
                    if self.db.case_exists(case.id):
                        skipped += 1
                        continue
                    
                    # 保存到数据库
                    self.db.insert_case(case)
                    imported += 1
                    case_ids.append(case.id)
                    
                except Exception as e:
                    print(f"Failed to import case {i}: {e}")
                    failed += 1
            
            # 2. AI 分类（如果启用）
            if enable_ai_classify and case_ids:
                try:
                    self.task_store.update_stage(task_id, "classify", 0, len(case_ids), current_action=f"AI分类中... (0/{len(case_ids)})")
                except Exception:
                    pass
                self._perform_ai_classification(task_id, case_ids, total_cases)
            
            # 3. AI 聚类（如果启用）
            if enable_ai_clustering and len(case_ids) >= 2:
                # keep processed_cases stable as real import progress
                try:
                    self.task_store.update_progress(
                        task_id,
                        total_cases,
                        current_action="AI聚类分析中...",
                    )
                except Exception:
                    pass
                self._perform_ai_clustering(task_id, case_ids, total_cases)

            # 4. KG 抽取（导入后自动构建知识图谱）
            if case_ids:
                try:
                    self.task_store.update_stage(task_id, "kg_extract", 0, len(case_ids), current_action=f"知识图谱抽取中... (0/{len(case_ids)})")
                except Exception:
                    pass
                self._perform_kg_extraction(task_id, case_ids, total_cases)
            
            # 完成任务
            result = {
                "imported": imported,
                "skipped": skipped,
                "failed": failed,
                "case_ids": case_ids,
                "ai_classified": enable_ai_classify,
                "ai_clustered": enable_ai_clustering,
                "kg_extracted": True
            }
            
            self.task_store.update_status(task_id, "completed", result=result)

            try:
                self.task_store.update_stage(task_id, "completed", total_cases, total_cases, current_action="已完成")
            except Exception:
                pass
            
        except Exception as e:
            self.task_store.update_status(
                task_id, 
                "failed", 
                error_message=str(e)
            )
        finally:
            # 清理线程引用
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]
    
    def _build_case(self, case_data: Dict, default_domain: str) -> Case:
        """构建案例对象"""
        now = utc_now()
        
        # 生成 ID
        case_id = case_data.get('id', '')
        if not case_id:
            raw = json.dumps(case_data, ensure_ascii=False, sort_keys=True)
            case_id = f"case_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        
        return Case(
            id=case_id,
            domain=case_data.get('domain', default_domain) or default_domain or "GENERAL",
            title=case_data.get('title', 'Untitled'),
            description=case_data.get('description'),
            decision_node=case_data.get('decision_node'),
            action_taken=case_data.get('action_taken'),
            outcome_result=case_data.get('outcome_result'),
            outcome_timeline=case_data.get('outcome_timeline'),
            lesson_core=case_data.get('lesson_core'),
            confidence=case_data.get('confidence'),
            created_at=now,
            updated_at=now
        )
    
    def _perform_ai_classification(self, task_id: str, case_ids: List[str], total_cases: int):
        """执行 AI 分类"""
        return
    
    def _perform_ai_clustering(self, task_id: str, case_ids: List[str], total_cases: int):
        """执行 AI 聚类"""
        try:
            from ..ai.case_clustering import get_clustering_engine
            
            clustering = get_clustering_engine()
            if not clustering:
                print("AI clustering not available, skipping clustering")
                return
            
            self.task_store.update_progress(
                task_id,
                total_cases,
                current_action="AI聚类分析中..."
            )
            
            # 获取所有案例数据
            cases = []
            for case_id in case_ids:
                try:
                    case = self.db.get_case(case_id)
                    cases.append(case.model_dump())
                except:
                    pass
            
            if len(cases) >= 2:
                # 执行聚类
                clusters = clustering.cluster_cases(cases, min_cluster_size=2)
                print(f"AI clustering completed: {len(clusters)} clusters found")
                
        except Exception as e:
            print(f"AI clustering failed: {e}")

    def _perform_kg_extraction(self, task_id: str, case_ids: List[str], total_cases: int) -> None:
        """对指定案例进行实体关系抽取并写入 SQLite"""
        try:
            from ..ai.decision_assistant import AIDecisionAssistant
            from ..knowledge.kg_extractor import extract_kg_from_case

            provider = self.config.get("ai.provider", "api")
            model = self.config.get("ai.model", "gpt-4.1-mini")
            api_key = self.config.get("ai.api_key", "") or None
            api_base = self.config.get("ai.api_base", "") or None

            ai = AIDecisionAssistant(provider=provider, model=model, api_key=api_key, api_base=api_base)
            if not ai.check_available():
                return

            for i, case_id in enumerate(case_ids):
                try:
                    self.task_store.update_progress(
                        task_id,
                        total_cases,
                        current_case=case_id[:30],
                        current_action=f"知识图谱抽取中... ({i+1}/{len(case_ids)})",
                    )

                    try:
                        self.task_store.update_stage(task_id, "kg_extract", i + 1, len(case_ids))
                    except Exception:
                        pass

                    case = self.db.get_case(case_id)
                    text = "\n".join(
                        [
                            case.title or "",
                            case.description or "",
                            case.decision_node or "",
                            case.action_taken or "",
                            case.outcome_result or "",
                            case.lesson_core or "",
                        ]
                    ).strip()
                    if not text:
                        continue

                    # 增量更新：如果文本未变化则跳过
                    sha1 = hashlib.sha1(text.encode("utf-8")).hexdigest()
                    state = self.db.get_kg_case_state(case.id)
                    if state and state.get("text_sha1") == sha1:
                        continue

                    ents, rels = extract_kg_from_case(
                        ai,
                        case_id=case.id,
                        title=case.title,
                        domain=case.domain,
                        text=text,
                    )

                    for e in ents:
                        self.db.upsert_entity(
                            entity_id=e["id"],
                            name=e["name"],
                            entity_type=e["type"],
                            attributes=e.get("attributes") or {},
                            updated_at=e.get("updated_at"),
                        )

                    for r in rels:
                        self.db.upsert_relation(
                            relation_id=r["id"],
                            source_entity_id=r["source"],
                            target_entity_id=r["target"],
                            relation_type=r["relation_type"],
                            confidence=float(r.get("confidence") or 0.5),
                            attributes=r.get("attributes") or {},
                            updated_at=r.get("updated_at"),
                        )

                        quote = str(r.get("quote") or "").strip()
                        if quote:
                            ev_id = f"ev_{r['id']}_{case.id}"[:64]
                            self.db.add_relation_evidence(
                                evidence_id=ev_id,
                                relation_id=r["id"],
                                case_id=case.id,
                                quote=quote[:2000],
                                start_offset=None,
                                end_offset=None,
                            )

                    # 记录抽取状态
                    self.db.upsert_kg_case_state(case_id=case.id, text_sha1=sha1)
                except Exception as e:
                    print(f"KG extraction failed for case {case_id}: {e}")

        except Exception as e:
            print(f"KG extraction failed: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.task_store.get_task(task_id)
    
    def is_task_active(self, task_id: str) -> bool:
        """检查任务是否在进行中"""
        task = self.task_store.get_task(task_id)
        if not task:
            return False
        return task['status'] in ['pending', 'processing']
