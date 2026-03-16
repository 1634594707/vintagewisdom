"""AI决策助手 - 支持本地Ollama和远程API"""

import json
import os
from typing import Dict, List, Optional, Tuple
import urllib.request

from ..models.case import Case


class AIDecisionAssistant:
    """AI决策助手，支持多种模型来源"""
    
    def __init__(
        self,
        provider: str = "ollama",  # "ollama" 或 "api"
        model: str = "qwen3.5:4b",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.api_base = api_base or os.getenv("AI_API_BASE", "")
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用本地Ollama"""
        try:
            base_url = "http://localhost:11434"
            data = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{base_url}/api/generate",
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')
        except Exception as e:
            print(f"Ollama call failed: {e}")
            return None
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """调用远程API（OpenAI格式）"""
        if not self.api_key or not self.api_base:
            return None
        
        try:
            data = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a decision-making assistant. Analyze cases and provide insights."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.api_base}/chat/completions",
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception as e:
            print(f"API call failed: {e}")
            return None
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """根据配置调用AI"""
        if self.provider == "ollama":
            return self._call_ollama(prompt)
        elif self.provider == "api":
            return self._call_api(prompt)
        return None
    
    def analyze_decision(
        self,
        query: str,
        cases: List[Case],
        context: Optional[Dict] = None
    ) -> Tuple[str, List[str]]:
        """
        分析决策并返回推理和建议
        
        Returns:
            (reasoning, recommendations)
        """
        # 如果没有匹配案例，直接使用AI分析查询本身
        if not cases:
            return self._analyze_without_cases(query)
        
        # 构建prompt
        cases_text = "\n\n".join([
            f"Case {i+1}:\n"
            f"Title: {case.title}\n"
            f"Domain: {case.domain}\n"
            f"Description: {case.description or 'N/A'}\n"
            f"Decision: {case.decision_node or 'N/A'}\n"
            f"Action: {case.action_taken or 'N/A'}\n"
            f"Outcome: {case.outcome_result or 'N/A'}\n"
            f"Lesson: {case.lesson_core or 'N/A'}"
            for i, case in enumerate(cases[:5])  # 最多5个案例
        ])
        
        prompt = f"""You are a decision-making assistant helping analyze a current decision based on historical cases.

Current Decision Query:
{query}

Historical Cases:
{cases_text}

Please provide:
1. Reasoning: Analyze how these historical cases relate to the current decision. What patterns do you see? What are the key risks and opportunities?
2. Recommendations: Provide 3-5 specific, actionable recommendations based on the lessons from these cases.

Format your response as:
REASONING:
[Your analysis here]

RECOMMENDATIONS:
1. [First recommendation]
2. [Second recommendation]
3. [Third recommendation]
..."""
        
        response = self._call_ai(prompt)
        
        if not response:
            # 回退到简单模板
            return (
                f"Found {len(cases)} similar case(s). Review outcomes before deciding.",
                ["Compare outcomes of similar cases.", "Identify key constraints and risks."]
            )
        
        # 解析响应
        reasoning = ""
        recommendations = []
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('REASONING:'):
                current_section = 'reasoning'
                continue
            elif line.upper().startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
                continue
            
            if current_section == 'reasoning' and line:
                reasoning += line + ' '
            elif current_section == 'recommendations' and line:
                # 移除序号前缀
                if line[0].isdigit() and line[1:3] in ['. ', ') ']:
                    line = line[3:].strip()
                if line:
                    recommendations.append(line)
        
        if not reasoning:
            reasoning = response[:500]  # 使用前500字符作为推理
        
        if not recommendations:
            recommendations = [
                "Compare outcomes of similar cases.",
                "Identify key constraints and risks.",
                "Consider the context differences between cases."
            ]
        
        return reasoning.strip(), recommendations[:5]
    
    def _analyze_without_cases(self, query: str) -> Tuple[str, List[str]]:
        """在没有历史案例的情况下，直接使用AI分析决策"""
        prompt = f"""你是一位经验丰富的决策顾问。用户面临以下决策情境，请提供专业的分析和建议。

决策情境：
{query}

请提供：
1. 分析：这个决策涉及哪些关键因素？可能的风险和机会是什么？
2. 建议：提供3-5条具体的、可操作的建议

输出格式：
分析：
[你的分析]

建议：
1. [第一条建议]
2. [第二条建议]
3. [第三条建议]
"""
        
        response = self._call_ai(prompt)
        
        if not response:
            # AI调用失败，返回通用建议
            return (
                "无法获取AI分析。这是一个关于投资决策的查询，涉及市场泡沫风险的评估。",
                [
                    "收集更多市场数据和信息，避免盲目决策",
                    "评估自身的风险承受能力",
                    "考虑分散投资以降低单一资产风险",
                    "设定明确的投资目标和止损点",
                    "咨询专业的投资顾问获取第二意见"
                ]
            )
        
        # 解析响应
        reasoning = ""
        recommendations = []
        
        lines = response.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('分析：') or line.upper().startswith('分析:'):
                current_section = 'reasoning'
                continue
            elif line.startswith('建议：') or line.upper().startswith('建议:'):
                current_section = 'recommendations'
                continue
            
            if current_section == 'reasoning' and line:
                reasoning += line + ' '
            elif current_section == 'recommendations' and line:
                # 移除序号前缀
                if line[0].isdigit() and line[1:3] in ['. ', ') ']:
                    line = line[3:].strip()
                if line and not line.startswith('建议'):
                    recommendations.append(line)
        
        if not reasoning:
            reasoning = response[:500]
        
        if not recommendations:
            recommendations = [
                "收集更多信息后再做决策",
                "评估可能的风险和收益",
                "咨询专业人士的意见"
            ]
        
        return reasoning.strip(), recommendations[:5]
    
    def check_available(self) -> bool:
        """检查AI服务是否可用"""
        if self.provider == "ollama":
            try:
                req = urllib.request.Request(
                    "http://localhost:11434/api/tags",
                    method='GET'
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status == 200
            except:
                return False
        elif self.provider == "api":
            return bool(self.api_key and self.api_base)
        return False


# 全局实例
_ai_assistant: Optional[AIDecisionAssistant] = None


def get_ai_assistant(
    provider: str = "ollama",
    model: str = "qwen3.5:4b",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None
) -> AIDecisionAssistant:
    """获取AI助手实例"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIDecisionAssistant(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base
        )
    return _ai_assistant


def update_ai_config(
    provider: str = "ollama",
    model: str = "qwen3.5:4b",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None
):
    """更新AI配置"""
    global _ai_assistant
    _ai_assistant = AIDecisionAssistant(
        provider=provider,
        model=model,
        api_key=api_key,
        api_base=api_base
    )
