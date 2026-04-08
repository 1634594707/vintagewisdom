"""领域分类和自动分类功能"""

from typing import Dict, List, Tuple

# 领域关键词映射（用于AI自动分类）
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "HIS-POL": ["政治", "制度", "权力", "运动"],
    "HIS-WAR": ["战争", "军事", "冲突", "战役"],
    "HIS-DIP": ["外交", "联盟", "谈判", "条约"],
    "HIS-ECO": ["经济政策", "财政", "货币", "治理"],
    "HIS-SOC": ["社会治理", "民生", "阶层", "改革"],
    "HIS-IDE": ["思想", "意识形态", "宣传", "舆论"],
    "FIN-INV": ["投资", "股票", "基金", "房产", "理财", "资产配置"],
    "FIN-MKT": ["市场", "交易", "投机", "行情", "价格"],
    "FIN-RISK": ["风险", "止损", "回撤", "风控"],
    "FIN-DEB": ["债务", "杠杆", "信用", "贷款", "违约"],
    "FIN-INS": ["保险", "保障", "理赔"],
    "FIN-MAC": ["宏观", "周期", "政策", "利率", "通胀"],
    "CAR-JOB": ["求职", "面试", "offer", "简历", "跳槽"],
    "CAR-TRA": ["转行", "转型", "职业切换"],
    "CAR-ADV": ["晋升", "升职", "成长"],
    "CAR-ENT": ["创业", "融资", "公司"],
    "CAR-NEG": ["谈判", "薪酬", "薪资", "股权"],
    "CAR-BAL": ["工作生活平衡", "加班", "倦怠"],
    "TEC-ARC": ["架构", "系统设计", "微服务"],
    "TEC-CHO": ["技术选型", "框架", "语言", "工具"],
    "TEC-REF": ["重构", "技术债", "代码质量"],
    "TEC-INN": ["创新", "研发", "新技术"],
    "TEC-OPS": ["运维", "可靠性", "性能", "安全", "DevOps"],
    "TEC-DAT": ["数据工程", "指标", "治理"],
}

# 领域层级结构
DOMAIN_HIERARCHY = {
    "HIS": {"name": "历史政治", "sub": ["POL", "WAR", "DIP", "ECO", "SOC", "IDE"]},
    "FIN": {"name": "财务金融", "sub": ["INV", "MKT", "RISK", "DEB", "INS", "MAC"]},
    "CAR": {"name": "职业发展", "sub": ["JOB", "TRA", "ADV", "ENT", "NEG", "BAL"]},
    "TEC": {"name": "技术工程", "sub": ["ARC", "CHO", "REF", "INN", "OPS", "DAT"]},
}


def auto_classify_domain(text: str, use_ai: bool = True, timeout: int = 30) -> List[Dict]:
    """自动分类领域
    
    Args:
        text: 要分类的文本
        use_ai: 是否尝试使用AI模型（如果可用）
        timeout: AI调用超时时间（秒）
    
    Returns:
        List of {"domain": str, "confidence": float, "reason": str}
    """
    # 线上版不再内置本地模型分类，保持显式空返回。
    return []


def get_main_domain(sub_code: str) -> str:
    """获取子领域对应的主领域代码"""
    if "-" in sub_code:
        return sub_code.split("-")[0]
    return sub_code


def get_domain_name(code: str) -> str:
    """获取领域名称"""
    if "-" in code:
        main_code, sub_code = code.split("-", 1)
        main_info = DOMAIN_HIERARCHY.get(main_code, {})
        sub_list = main_info.get("sub", [])
        if sub_code in sub_list:
            return f"{main_info.get('name', main_code)}-{sub_code}"
    return DOMAIN_HIERARCHY.get(code, {}).get("name", code)


def calculate_similarity(case1: Dict, case2: Dict) -> Tuple[float, List[str]]:
    """计算两个案例之间的相似度
    
    Returns:
        (similarity_score, reasons)
    """
    similarity = 0.0
    reasons = []
    
    # 1. 相同domain (+40%)
    domain1 = case1.get("domain", "")
    domain2 = case2.get("domain", "")
    
    if domain1 and domain2:
        if domain1 == domain2:
            similarity += 0.4
            reasons.append("相同领域")
        else:
            # 检查是否属于同一主领域
            main1 = get_main_domain(domain1)
            main2 = get_main_domain(domain2)
            if main1 == main2:
                similarity += 0.2
                reasons.append("同主领域")
    
    # 2. 标题相似度 (+10% per common word)
    title1 = case1.get("title", "").lower()
    title2 = case2.get("title", "").lower()
    
    if title1 and title2:
        words1 = set(title1.split())
        words2 = set(title2.split())
        common_words = words1 & words2
        
        # 过滤短词
        meaningful_words = {w for w in common_words if len(w) > 1}
        
        if meaningful_words:
            title_sim = min(len(meaningful_words) * 0.1, 0.3)
            similarity += title_sim
            reasons.append(f"标题关键词匹配: {', '.join(list(meaningful_words)[:3])}")
    
    # 3. 描述相似度（简单实现）
    desc1 = case1.get("description", "") or ""
    desc2 = case2.get("description", "") or ""
    
    if desc1 and desc2:
        desc1_lower = desc1.lower()
        desc2_lower = desc2.lower()
        
        # 检查是否有共同的关键词
        common_keywords = []
        for keyword_list in DOMAIN_KEYWORDS.values():
            for keyword in keyword_list:
                if keyword in desc1_lower and keyword in desc2_lower:
                    common_keywords.append(keyword)
        
        if common_keywords:
            desc_sim = min(len(common_keywords) * 0.05, 0.2)
            similarity += desc_sim
            reasons.append(f"描述关键词匹配: {len(common_keywords)}个")
    
    return round(min(similarity, 1.0), 2), reasons


def find_similar_cases(cases: List[Dict], target_case: Dict, threshold: float = 0.3) -> List[Dict]:
    """查找与目标案例相似的案例
    
    Returns:
        List of {"case_id": str, "similarity": float, "reasons": List[str]}
    """
    similar_cases = []
    
    for case in cases:
        if case.get("id") == target_case.get("id"):
            continue
        
        similarity, reasons = calculate_similarity(target_case, case)
        
        if similarity >= threshold:
            similar_cases.append({
                "case_id": case.get("id"),
                "similarity": similarity,
                "reasons": reasons
            })
    
    # 按相似度排序
    similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
    return similar_cases
