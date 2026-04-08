"""AI决策助手 - 仅支持远程API"""

from typing import Dict, List, Optional, Tuple

from ..models.case import Case
from ..core.llm import LLMService


class AIDecisionAssistant:
    """AI决策助手，基于远程 API"""
    
    def __init__(
        self,
        provider: str = "api",
        model: str = "gpt-4.1-mini",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout_s: int = 30,
        retries: int = 1,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self._llm = LLMService(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base,
            timeout_s=timeout_s,
            retries=retries,
        )
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """调用远程API（OpenAI格式）"""
        if self.provider != "api":
            return None
        if not self._llm.api_key or not self._llm.api_base:
            return None
        try:
            messages = [
                {"role": "system", "content": "你是一位中文决策助手。请始终使用简体中文输出，内容要具体、克制、可执行。"},
                {"role": "user", "content": prompt},
            ]
            return self._llm.chat(messages, temperature=0.7)
        except Exception as e:
            print(f"API call failed: {e}")
            return None
    
    def _call_ai(self, prompt: str) -> Optional[str]:
        """根据配置调用AI"""
        if self.provider == "api":
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
        
        prompt = f"""你是一位中文决策助手，请基于历史案例为当前问题给出判断。

当前问题：
{query}

相关历史案例：
{cases_text}

请严格使用中文，并按下面格式输出：

分析：
先用 2 到 4 段说明这些案例与当前问题的相似点、关键差异、主要风险和机会。

建议：
1. 给出 3 到 5 条具体、可执行、能落地的建议。
2. 每条建议尽量短句表达，避免空话。
3. 不要输出英文标题，不要输出额外说明。"""
        
        response = self._call_ai(prompt)
        
        if not response:
            # 回退到简单模板
            return (
                f"系统找到了 {len(cases)} 个相似案例。先比较它们的结果分化，再决定当前问题更适合一次性推进，还是分阶段落地。",
                [
                    "先比较相似案例的最终结果，确认哪些做法真正带来了改善。",
                    "把当前约束条件写清楚，尤其是交付压力、时间窗口和团队承受能力。",
                    "优先选择可回退、可分阶段验证的路径，避免一次性押注。",
                ]
            )
        
        # 解析响应
        reasoning = ""
        recommendations = []
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith('REASONING:') or line.startswith('分析：') or line.startswith('分析:'):
                current_section = 'reasoning'
                continue
            elif line.upper().startswith('RECOMMENDATIONS:') or line.startswith('建议：') or line.startswith('建议:'):
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
                "先对照相似案例的结果，避免只看过程不看结局。",
                "把关键约束和风险写成清单，再决定优先级。",
                "关注当前情境与历史案例之间的差异，不要生搬硬套。"
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
        return self._llm.check_available()


# 全局实例
_ai_assistant: Optional[AIDecisionAssistant] = None


def get_ai_assistant(
    provider: str = "api",
    model: str = "gpt-4.1-mini",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    timeout_s: int = 30,
    retries: int = 1,
) -> AIDecisionAssistant:
    """获取AI助手实例"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIDecisionAssistant(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base,
            timeout_s=timeout_s,
            retries=retries,
        )
    return _ai_assistant


def update_ai_config(
    provider: str = "api",
    model: str = "gpt-4.1-mini",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    timeout_s: int = 30,
    retries: int = 1,
):
    """更新AI配置"""
    global _ai_assistant
    _ai_assistant = AIDecisionAssistant(
        provider=provider,
        model=model,
        api_key=api_key,
        api_base=api_base,
        timeout_s=timeout_s,
        retries=retries,
    )
