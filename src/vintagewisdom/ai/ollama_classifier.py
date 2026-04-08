"""Ollama AI 分类器 - 使用本地大模型进行领域分类"""

import json
import re
from typing import Dict, List, Optional
import urllib.request
import urllib.error


class OllamaClassifier:
    """使用Ollama本地模型进行领域分类"""
    
    def __init__(self, model: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

    def _compute_timeout_seconds(self, text: str) -> int:
        """按文本长度动态设置超时。

        经验公式：
        - 基础 30s
        - 每 200 字符 + 1s
        - 最小 30s，最大 180s
        """
        try:
            n = len(text or "")
        except Exception:
            n = 0
        t = 30 + int(n / 200)
        return max(30, min(180, t))
    
    def _call_ollama(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """调用Ollama API"""
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
    
    def classify_domain(self, text: str, timeout: int = 0) -> List[Dict]:
        """
        使用AI模型分类文本到领域
        
        Args:
            text: 要分类的文本
            timeout: 超时时间（秒）
        
        Returns:
            List of {"domain": str, "confidence": float, "reason": str}
        """
        prompt = f"""你是一位服务“案例导入”的领域分类助手，目标是把原始材料稳定映射到 VintageWisdom 的领域体系。
你的原则是：准确优先、宁缺毋滥、适合落库，不为了“看起来聪明”而乱贴标签。

要求：
1) 只允许输出下列领域代码（必须严格匹配），禁止自创任何代码。

主领域（一级）：HIS / FIN / CAR / TEC

二级（可选，推荐尽量给二级；不确定时只给一级）：

HIS（历史政治）
- HIS-POL: 政治制度/权力结构/政治运动
- HIS-WAR: 战争/军事/冲突
- HIS-DIP: 外交/联盟/谈判
- HIS-ECO: 经济政策/财政货币/治理
- HIS-SOC: 社会治理/民生/阶层
- HIS-IDE: 思想/意识形态/宣传

FIN（财务金融）
- FIN-INV: 投资与资产配置
- FIN-MKT: 市场行为/交易/投机
- FIN-RISK: 风险管理/止损/回撤
- FIN-DEB: 债务/杠杆/信用
- FIN-INS: 保险/保障
- FIN-MAC: 宏观周期/政策对市场

CAR（职业发展）
- CAR-JOB: 求职/跳槽/offer
- CAR-TRA: 转型/转行
- CAR-ADV: 晋升/成长
- CAR-ENT: 创业
- CAR-NEG: 谈判/薪酬
- CAR-BAL: 工作生活平衡

TEC（技术工程）
- TEC-ARC: 架构设计
- TEC-CHO: 技术选型
- TEC-REF: 重构/技术债
- TEC-INN: 技术创新
- TEC-OPS: 运维/可靠性/性能/安全
- TEC-DAT: 数据工程/指标/治理

2) primary_domain 必须且只能从 HIS/FIN/CAR/TEC 里选 1 个。
3) tags 为二级标签数组，总数 0-3 个；置信度<0.6 的标签绝对禁止输出。
4) tags 内所有二级标签必须归属 primary_domain；跨领域标签绝对禁止。
5) 如果材料信息不足，就少给标签，不要强行猜测。
6) 输出必须是严格 JSON，不要包含任何额外文字。

文本：
{text[:2000]}

输出 JSON schema：
{{
  "primary_domain": "HIS|FIN|CAR|TEC",
  "tags": [
    {{"code": "HIS-POL", "confidence": 0.80, "reason": "理由限30字内"}}
  ]
}}
"""
        
        use_timeout = int(timeout) if timeout and timeout > 0 else self._compute_timeout_seconds(text)
        response = self._call_ollama(prompt, timeout=use_timeout)
        
        if not response:
            return []
        
        return self._parse_response(response)
    
    def _parse_response(self, response: str) -> List[Dict]:
        """解析AI响应（严格 JSON + 枚举校验）"""
        try:
            raw = response.strip()
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                raw = raw[start : end + 1]
            data = json.loads(raw)
        except Exception:
            return []

        allowed_prefix = {"HIS", "FIN", "CAR", "TEC"}
        allowed_codes = {
            "HIS",
            "HIS-POL",
            "HIS-WAR",
            "HIS-DIP",
            "HIS-ECO",
            "HIS-SOC",
            "HIS-IDE",
            "FIN",
            "FIN-INV",
            "FIN-MKT",
            "FIN-RISK",
            "FIN-DEB",
            "FIN-INS",
            "FIN-MAC",
            "CAR",
            "CAR-JOB",
            "CAR-TRA",
            "CAR-ADV",
            "CAR-ENT",
            "CAR-NEG",
            "CAR-BAL",
            "TEC",
            "TEC-ARC",
            "TEC-CHO",
            "TEC-REF",
            "TEC-INN",
            "TEC-OPS",
            "TEC-DAT",
        }

        def norm_code(v: object) -> str:
            return str(v or "").strip().upper()

        def clamp_conf(v: object) -> float:
            try:
                x = float(v or 0.0)
            except Exception:
                x = 0.0
            return max(0.0, min(1.0, x))

        def short_reason(v: object) -> str:
            r = str(v or "").strip()
            if len(r) > 30:
                return r[:30]
            return r

        primary = norm_code(data.get("primary_domain") or data.get("primary") or data.get("domain") or "")
        if primary and primary not in allowed_codes:
            primary = ""
        if primary and primary.split("-", 1)[0] not in allowed_prefix:
            primary = ""
        # If model mistakenly outputs secondary as primary, keep only the main prefix.
        if primary and "-" in primary:
            primary = primary.split("-", 1)[0]

        tags_in = data.get("tags")
        if tags_in is None:
            tags_in = data.get("suggestions")
        if tags_in is None:
            tags_in = []
        if not isinstance(tags_in, list):
            return []

        primary_item: Optional[Dict[str, object]] = None
        secondary_items: List[Dict[str, object]] = []

        for item in tags_in:
            if not isinstance(item, dict):
                continue
            code = norm_code(item.get("code") or item.get("domain"))
            if not code:
                continue
            if code not in allowed_codes:
                continue
            main = code.split("-", 1)[0]
            if main not in allowed_prefix:
                continue

            conf = clamp_conf(item.get("confidence"))
            if conf < 0.6:
                continue

            record = {
                "domain": code,
                "confidence": round(conf, 2),
                "reason": short_reason(item.get("reason")),
            }

            if "-" not in code:
                # Treat as primary suggestion.
                if primary_item is None or float(record["confidence"]) > float(primary_item.get("confidence") or 0.0):
                    primary_item = record
            else:
                secondary_items.append(record)

        # Decide primary (accuracy-first): prefer explicit primary, else inferred from top candidate.
        if not primary:
            if primary_item:
                primary = str(primary_item.get("domain") or "")
            elif secondary_items:
                primary = str(secondary_items[0].get("domain") or "").split("-", 1)[0]

        # Keep only secondary tags that belong to the primary main domain.
        if primary:
            pmain = primary.split("-", 1)[0]
            secondary_items = [x for x in secondary_items if str(x.get("domain") or "").split("-", 1)[0] == pmain]

        secondary_items.sort(key=lambda x: float(x.get("confidence") or 0.0), reverse=True)
        secondary_items = secondary_items[:3]

        out: List[Dict] = []
        if primary:
            # Provide a primary entry for downstream compatibility (engine uses results[0]).
            if primary_item and str(primary_item.get("domain") or "") == primary:
                out.append({
                    "domain": primary,
                    "confidence": float(primary_item.get("confidence") or 0.0),
                    "reason": str(primary_item.get("reason") or ""),
                })
            else:
                out.append({"domain": primary, "confidence": 0.6, "reason": ""})

        out.extend(secondary_items)
        # Final safety: enforce max 3 overall.
        return out[:3]
    
    def check_available(self) -> bool:
        """检查Ollama是否可用"""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False


# 全局分类器实例
_ollama_classifier: Optional[OllamaClassifier] = None


def get_ollama_classifier(model: str = "qwen3.5:4b") -> Optional[OllamaClassifier]:
    """获取Ollama分类器实例"""
    global _ollama_classifier
    if _ollama_classifier is None:
        classifier = OllamaClassifier(model=model)
        if classifier.check_available():
            _ollama_classifier = classifier
        else:
            return None
    return _ollama_classifier


def ai_classify_domain(text: str, model: str = "deepseek-r1:7b", timeout: int = 0) -> List[Dict]:
    """
    使用AI模型分类领域
    
    Args:
        text: 要分类的文本
        model: Ollama模型名称
        timeout: 超时时间（秒）
        
    Returns:
        分类结果列表
    """
    classifier = get_ollama_classifier(model)
    
    if classifier is None:
        return []
    
    return classifier.classify_domain(text, timeout=timeout)
