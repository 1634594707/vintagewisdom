from __future__ import annotations


class RedTeam:
    def run(self, query: str) -> str:
        q = (query or "").strip()
        if not q:
            return ""

        # MVP: deterministic critique template (no external AI dependency)
        parts: list[str] = []
        parts.append("1) 事实基础：你依赖的关键事实/数据是什么？是否可验证？")
        parts.append("2) 反例检索：有哪些历史案例或证据会反驳当前倾向？")
        parts.append("3) 隐含假设：你的默认假设有哪些？哪些一旦不成立会导致决策失败？")
        parts.append("4) 极端情境：最坏情况会怎样？你是否有止损/撤退方案？")
        parts.append("5) 机会成本：不做/延后/替代方案分别会损失什么？")
        parts.append("6) 可逆性：这件事的可逆程度如何？如何把不可逆部分拆成可逆步骤？")
        return "\n".join(parts)
