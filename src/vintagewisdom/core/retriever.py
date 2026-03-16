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
        candidates = self.db.list_cases()
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
    
    def _semantic_match(self, query: str, candidates: List[Case]) -> List[tuple[float, Case]]:
        """使用AI进行语义匹配"""
        scored = []
        
        # 尝试使用AI分类查询的领域
        try:
            from ..ai.ollama_classifier import ai_classify_domain
            query_domains = ai_classify_domain(query, timeout=10)
            
            if query_domains:
                query_domain = query_domains[0]['domain']
                
                # 根据领域匹配案例
                for case in candidates:
                    score = 0
                    
                    # 相同领域加分
                    if case.domain and case.domain.upper() == query_domain.upper():
                        score += 100
                    # 同一大类加分
                    elif case.domain and case.domain.split('-')[0].upper() == query_domain.split('-')[0].upper():
                        score += 50

                    # Multi-label tags bonus (if present)
                    try:
                        if getattr(case, "domain_tags", None):
                            tags = json.loads(case.domain_tags) if isinstance(case.domain_tags, str) else []
                            if isinstance(tags, list):
                                tag_codes = [str(t.get("domain") or t.get("code") or "").upper() for t in tags if isinstance(t, dict)]
                                if query_domain.upper() in tag_codes:
                                    score += 80
                                else:
                                    qmain = query_domain.split("-", 1)[0].upper()
                                    if any(c.split("-", 1)[0].upper() == qmain for c in tag_codes if c):
                                        score += 30
                    except Exception:
                        pass
                    
                    if score > 0:
                        scored.append((score, case))
        except Exception as e:
            print(f"Semantic match failed: {e}")
        
        # 如果AI匹配也失败，返回所有案例（低分）
        if not scored:
            for case in candidates:
                scored.append((1, case))
        
        return scored
