from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..models.case import Case
from ..models.decision import DecisionLog
from ..storage.database import Database
from ..utils.config import Config
from ..utils.helpers import ensure_dir, resolve_data_dir
from ..utils.logger import get_logger
from .retriever import Retriever


@dataclass
class QueryResult:
    cases: List[Case]
    reasoning: str
    recommendations: List[str]


class Engine:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.log = get_logger("vintagewisdom.engine")
        self.db = Database(self._resolve_db_path())
        self.retriever = Retriever(self.db)
        
        # 初始化AI助手
        self._init_ai_assistant()

    def _init_ai_assistant(self):
        """初始化AI决策助手"""
        from ..ai.decision_assistant import AIDecisionAssistant
        
        # 从配置中读取AI设置
        ai_provider = self.config.get("ai.provider", "api")
        ai_model = self.config.get("ai.model", "gpt-4.1-mini")
        ai_api_key = self.config.get("ai.api_key", "")
        ai_api_base = self.config.get("ai.api_base", "")
        ai_timeout = self.config.get("ai.timeout_s", 30)
        ai_retries = self.config.get("ai.retries", 1)
        
        self.ai_assistant = AIDecisionAssistant(
            provider=ai_provider,
            model=ai_model,
            api_key=ai_api_key if ai_api_key else None,
            api_base=ai_api_base if ai_api_base else None,
            timeout_s=int(ai_timeout or 30),
            retries=int(ai_retries or 1),
        )
        
        if self.ai_assistant.check_available():
            self.log.info(f"AI assistant initialized with provider: {ai_provider}, model: {ai_model}")
        else:
            self.log.warning(f"AI assistant not available for provider: {ai_provider}")

    def _resolve_db_path(self) -> Path:
        configured = self.config.get("storage.database_path", "data/vintagewisdom.db")
        configured_path = Path(configured)
        data_dir = resolve_data_dir(configured_path.parent)
        ensure_dir(data_dir)
        return data_dir / configured_path.name

    def initialize(self) -> None:
        self.db.initialize()
        self.log.info("Initialized database at %s", self.db.path)

    def add_case(self, case: Case) -> None:
        from .events import events

        events.emit("case.adding", {"case": case})
        self.db.insert_case(case)
        events.emit("case.added", {"case": case})

    def log_decision(self, log: DecisionLog) -> None:
        self.db.insert_decision_log(log)

    def evaluate_decision(self, decision_id: str, actual_outcome: str) -> None:
        self.db.evaluate_decision_log(decision_id=decision_id, actual_outcome=actual_outcome)

    def query(self, text: str) -> QueryResult:
        """查询决策建议"""
        from .events import events

        before_payload = {"text": text, "engine": self, "context": {}}
        try:
            events.emit("decision.before", before_payload)
        except Exception:
            pass

        cases = self.retriever.retrieve(text)
        
        # 使用AI助手分析决策
        reasoning, recommendations = self.ai_assistant.analyze_decision(text, cases)

        after_payload = {
            "text": text,
            "engine": self,
            "cases": cases,
            "reasoning": reasoning,
            "recommendations": list(recommendations),
            "context": before_payload.get("context") if isinstance(before_payload.get("context"), dict) else {},
        }
        try:
            events.emit("decision.after", after_payload)
        except Exception:
            pass

        reasoning = str(after_payload.get("reasoning") or reasoning)
        recs = after_payload.get("recommendations")
        if isinstance(recs, list):
            recommendations = [str(x) for x in recs if str(x).strip()]
        
        return QueryResult(cases=cases, reasoning=reasoning, recommendations=recommendations)
    
    def update_ai_config(
        self,
        provider: str = "api",
        model: str = "gpt-4.1-mini",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None
    ):
        """更新AI配置"""
        from ..ai.decision_assistant import AIDecisionAssistant
        
        self.ai_assistant = AIDecisionAssistant(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base
        )
        
        # 更新配置文件
        self.config.set("ai.provider", provider)
        self.config.set("ai.model", model)
        if api_key:
            self.config.set("ai.api_key", api_key)
        if api_base:
            self.config.set("ai.api_base", api_base)
        
        self.log.info(f"AI config updated: provider={provider}, model={model}")
