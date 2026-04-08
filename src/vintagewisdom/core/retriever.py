from __future__ import annotations

from typing import List, Optional

from ..models.case import Case
from ..storage.database import Database


class Retriever:
    def __init__(self, db: Database):
        self.db = db

    def retrieve(self, query: str, top_k: int = 5) -> List[Case]:
        """检索相关案例
        
        使用多种策略：
        1. 关键词匹配
        2. 语义相似度（通过AI）
        3. 领域匹配
        """
        candidates = [case for case in self.db.list_cases() if not self._is_test_case(case)]
        if not candidates:
            return []
        
        if not query:
            return candidates[:top_k]
        
        query_lower = query.lower()
        
        # 策略1: 关键词匹配
        scored: List[tuple[float, Case]] = []
        for case in candidates:
            text = f"{case.title} {case.description or ''} {case.domain or ''}".lower()
            
            # 基础分数：关键词出现次数
            score = text.count(query_lower) * 10
            
            # 标题匹配权重更高
            if query_lower in case.title.lower():
                score += 50
            
            # 领域匹配
            if case.domain:
                # 查询中包含领域关键词
                domain_keywords = {
                    'fin': ['投资', '理财', '股票', '基金', '金融', '财务', '钱', '资产', '收益', '股市', '泡沫'],
                    'car': ['工作', '职业', '求职', '面试', '简历', '升职', '跳槽', '创业', '薪资'],
                    'tec': ['技术', '架构', '代码', '编程', '系统', '软件', '开发', '工程师'],
                    'mgt': ['管理', '团队', '项目', '领导', '组织', '决策', '规划'],
                    'rel': ['关系', '感情', '朋友', '家庭', '沟通', '社交', '人际'],
                    'hea': ['健康', '运动', '饮食', '睡眠', '心理', '身体', '医疗'],
                    'edu': ['学习', '教育', '技能', '培训', '知识', '考试', '证书'],
                    'lif': ['生活', '时间', '居住', '旅行', '消费', '价值观'],
                }
                
                domain_prefix = case.domain.lower().split('-')[0]
                if domain_prefix in domain_keywords:
                    for keyword in domain_keywords[domain_prefix]:
                        if keyword in query_lower:
                            score += 20
                            break
            
            # 如果分数大于0，加入结果
            if score > 0:
                scored.append((score, case))
        
        # 如果没有关键词匹配，尝试AI语义匹配
        if not scored:
            scored = self._semantic_match(query, candidates)
        
        # 按分数排序
        scored.sort(key=lambda item: item[0], reverse=True)
        return [case for _, case in scored[:top_k]]

    def _is_test_case(self, case: Case) -> bool:
        case_id = (case.id or "").strip().lower()
        title = (case.title or "").strip().lower()
        description = (case.description or "").strip().lower()
        return (
            case_id.startswith("case_test_")
            or case_id.startswith("test-")
            or title == "test case"
            or title.startswith("测试案例")
            or description == "just a test"
        )
    
    def _semantic_match(self, query: str, candidates: List[Case]) -> List[tuple[float, Case]]:
        """语义匹配降级实现（无本地模型依赖）"""
        scored = []

        # 无额外模型可用时，返回统一低分候选。
        if not scored:
            for case in candidates:
                scored.append((1, case))
        
        return scored
