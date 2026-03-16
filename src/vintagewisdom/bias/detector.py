from __future__ import annotations

from typing import List


class BiasDetector:
    def detect(self, text: str) -> List[str]:
        t = (text or "").strip()
        if not t:
            return []

        out: List[str] = []
        lower = t.lower()

        # Confirmation bias / overconfidence
        if any(w in t for w in ["肯定", "一定", "绝对", "百分百", "毫无疑问", "必然"]):
            out.append("确认偏误/过度自信")

        # Planning fallacy
        if any(w in t for w in ["很快", "不难", "简单", "轻松", "马上", "一天搞定", "两天搞定"]):
            out.append("计划谬误")

        # Sunk cost
        if any(w in t for w in ["都已经", "已经投入", "沉没成本", "不甘心", "不能白费", "都做到这一步"]):
            out.append("沉没成本")

        # Recency / availability
        if any(w in t for w in ["最近", "刚刚", "这两天", "这周", "这次", "上一回"]):
            out.append("近因效应")

        # Loss aversion
        if any(w in t for w in ["怕亏", "不能亏", "损失", "亏损", "下跌", "回撤"]):
            out.append("损失厌恶")

        # Simple de-dup
        uniq: List[str] = []
        for x in out:
            if x not in uniq:
                uniq.append(x)
        return uniq
