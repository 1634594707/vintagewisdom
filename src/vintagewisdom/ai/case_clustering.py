"""
AI 案例聚类和关联分析模块
使用本地大模型进行语义聚类和相似度计算
"""

import json
import urllib.request
from typing import Dict, List, Optional, Tuple
import re


class CaseClustering:
    """使用 AI 进行案例聚类和关联分析"""
    
    def __init__(self, model: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def _call_ollama(self, prompt: str, timeout: int = 60) -> Optional[str]:
        """调用 Ollama API"""
        try:
            data = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }).encode('utf-8')
            
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')
        except Exception as e:
            print(f"Ollama API call failed: {e}")
            return None
    
    def extract_case_features(self, case: Dict) -> Dict:
        """提取案例特征用于聚类"""
        # 组合案例的关键信息
        text_parts = []
        
        if case.get('title'):
            text_parts.append(f"案例名称: {case['title']}")
        if case.get('decision_node'):
            text_parts.append(f"决策节点: {case['decision_node']}")
        if case.get('description'):
            text_parts.append(f"描述: {case['description']}")
        if case.get('lesson_core'):
            text_parts.append(f"教训: {case['lesson_core']}")
        
        return {
            'id': case.get('id', ''),
            'text': '\n'.join(text_parts),
            'domain': case.get('domain', ''),
        }
    
    def calculate_semantic_similarity(self, case1: Dict, case2: Dict) -> Tuple[float, List[str]]:
        """
        使用 AI 计算两个案例的语义相似度
        
        Returns:
            (similarity_score, reasons)
        """
        feat1 = self.extract_case_features(case1)
        feat2 = self.extract_case_features(case2)
        
        prompt = f"""分析以下两个决策案例的相似程度。

## 案例 A
{feat1['text'][:800]}

## 案例 B
{feat2['text'][:800]}

## 分析要求
请判断这两个案例在以下维度上的相似性：
1. 决策类型（如：投资交易、技术架构、团队管理等）
2. 风险模式（如：过度自信、缺乏风控、盲目跟风等）
3. 失败原因（如：杠杆过高、架构不合理、管理失误等）
4. 教训启示（如：止损重要性、架构演进、团队建设等）

## 输出格式
请只返回以下格式：

相似度: 0-100之间的数字（如75）
原因: 一句话说明相似的核心原因

例如：
相似度: 85
原因: 两者都是投资交易中因过度自信和缺乏风控导致的爆仓案例"""

        response = self._call_ollama(prompt, timeout=30)
        
        if not response:
            # 如果 AI 调用失败，回退到基于 domain 的简单计算
            return self._fallback_similarity(case1, case2)
        
        # 解析响应
        similarity = 0.5
        reasons = []
        
        # 提取相似度数字
        match = re.search(r'相似度[:：]\s*(\d+)', response)
        if match:
            similarity = int(match.group(1)) / 100
        
        # 提取原因
        reason_match = re.search(r'原因[:：]\s*(.+?)(?:\n|$)', response)
        if reason_match:
            reasons.append(reason_match.group(1).strip())
        
        return round(similarity, 2), reasons
    
    def _fallback_similarity(self, case1: Dict, case2: Dict) -> Tuple[float, List[str]]:
        """当 AI 不可用时，使用基于 domain 的简单相似度计算"""
        from ..knowledge.domains import calculate_similarity
        return calculate_similarity(case1, case2)
    
    def find_similar_cases_batch(
        self, 
        target_case: Dict, 
        candidate_cases: List[Dict], 
        threshold: float = 0.5,
        top_k: int = 5
    ) -> List[Dict]:
        """
        批量查找相似案例（优化版本，使用一次 AI 调用）
        
        Args:
            target_case: 目标案例
            candidate_cases: 候选案例列表
            threshold: 相似度阈值
            top_k: 返回最相似的 k 个
        
        Returns:
            List of {"case_id": str, "similarity": float, "reasons": List[str]}
        """
        if not candidate_cases:
            return []
        
        target_feat = self.extract_case_features(target_case)
        
        # 构建候选案例文本
        candidates_text = []
        for i, case in enumerate(candidate_cases[:20]):  # 限制候选数量避免 prompt 过长
            feat = self.extract_case_features(case)
            candidates_text.append(f"""
[{i}] ID: {case.get('id', '')}
名称: {case.get('title', '')}
类型: {case.get('domain', '')}
描述: {feat['text'][:300]}...""")
        
        prompt = f"""分析以下目标案例与候选案例的相似度。

## 目标案例
{target_feat['text'][:600]}

## 候选案例
{''.join(candidates_text)}

## 任务
请分析目标案例与每个候选案例的相似度（0-100分），重点关注：
1. 决策类型是否相同
2. 失败原因是否相似
3. 风险模式是否一致
4. 教训是否相通

## 输出格式
请只返回相似度大于50分的候选案例，格式如下：

[案例编号]: [相似度分数]
原因: [一句话说明]

例如：
[0]: 85
原因: 两者都是投资交易中因过度自信导致的爆仓

[2]: 70
原因: 都涉及高杠杆和缺乏风控的问题"""

        response = self._call_ollama(prompt, timeout=60)
        
        results = []
        if response:
            # 解析响应
            pattern = r'\[(\d+)\][:：]\s*(\d+)'
            matches = re.findall(pattern, response)
            
            for idx_str, score_str in matches:
                idx = int(idx_str)
                score = int(score_str) / 100
                
                if idx < len(candidate_cases) and score >= threshold:
                    case = candidate_cases[idx]
                    
                    # 提取该案例的原因
                    case_pattern = rf'\[{idx}\][:：]\s*\d+\s*原因[:：](.+?)(?=\[|$)'
                    case_match = re.search(case_pattern, response, re.DOTALL)
                    reason = case_match.group(1).strip() if case_match else "AI分析相似"
                    
                    results.append({
                        'case_id': case.get('id', ''),
                        'similarity': round(score, 2),
                        'reasons': [reason]
                    })
        
        # 如果 AI 没有返回结果，回退到传统方法
        if not results:
            from ..knowledge.domains import find_similar_cases
            all_cases_dict = [{**c, 'id': c.get('id', '')} for c in candidate_cases]
            results = find_similar_cases(all_cases_dict, target_case, threshold)
        
        # 排序并限制数量
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def cluster_cases(self, cases: List[Dict], min_cluster_size: int = 2) -> List[Dict]:
        """
        对案例进行聚类，返回聚类结果
        
        Returns:
            List of {"cluster_id": str, "cluster_name": str, "cases": List[case_id], "theme": str}
        """
        if len(cases) < min_cluster_size:
            return []
        
        # 构建案例摘要
        case_summaries = []
        for i, case in enumerate(cases[:15]):  # 限制数量
            case_summaries.append(f"""
[{i}] {case.get('title', '')}
领域: {case.get('domain', '')}
决策节点: {case.get('decision_node', '')}
教训: {case.get('lesson_core', '')[:100]}...""")
        
        prompt = f"""对以下决策案例进行聚类分析，将相似的案例归为一组。

## 案例列表
{''.join(case_summaries)}

## 聚类任务
请将这些案例分成 2-4 个聚类，每个聚类应该包含相似的案例（至少2个）。
考虑以下维度进行聚类：
1. 决策领域（投资、技术、管理等）
2. 失败模式（过度自信、缺乏风控、盲目跟风等）
3. 风险类型（杠杆、架构、团队等）

## 输出格式
请按以下格式返回：

聚类1: [聚类名称]
案例: [编号1], [编号2], ...
主题: [一句话描述这个聚类的核心主题]

聚类2: [聚类名称]
案例: [编号1], [编号2], ...
主题: [一句话描述]

例如：
聚类1: 投资交易爆仓类
案例: 0, 2, 5
主题: 高杠杆投资交易中因缺乏风控导致的爆仓案例

聚类2: 技术架构失误类
案例: 1, 3
主题: 技术系统架构设计不当导致的故障和损失"""

        response = self._call_ollama(prompt, timeout=60)
        
        clusters = []
        if response:
            # 解析聚类结果
            cluster_pattern = r'聚类\d+[:：]\s*(.+?)\n案例[:：]\s*([\d,\s]+)\n主题[:：]\s*(.+?)(?=\n\n聚类|\Z)'
            matches = re.findall(cluster_pattern, response, re.DOTALL)
            
            for i, (name, case_nums, theme) in enumerate(matches):
                case_indices = [int(x.strip()) for x in case_nums.split(',') if x.strip().isdigit()]
                case_ids = [cases[idx].get('id', '') for idx in case_indices if idx < len(cases)]
                
                if len(case_ids) >= min_cluster_size:
                    clusters.append({
                        'cluster_id': f'cluster_{i}',
                        'cluster_name': name.strip(),
                        'cases': case_ids,
                        'theme': theme.strip()
                    })
        
        return clusters
    
    def check_available(self) -> bool:
        """检查 Ollama 是否可用"""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False


# 全局聚类器实例
_clustering: Optional[CaseClustering] = None


def get_clustering_engine(model: str = "deepseek-r1:7b") -> Optional[CaseClustering]:
    """获取聚类引擎实例"""
    global _clustering
    if _clustering is None:
        engine = CaseClustering(model=model)
        if engine.check_available():
            _clustering = engine
        else:
            return None
    return _clustering
