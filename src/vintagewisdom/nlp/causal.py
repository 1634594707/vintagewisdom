from __future__ import annotations

import re
from typing import List


class CausalExtractor:
    def extract(self, text: str) -> List[str]:
        t = (text or "").strip()
        if not t:
            return []

        # MVP patterns: because/so and cause/effect connectors
        patterns = [
            r"因为(?P<cause>[^\n。；;]{1,80})所以(?P<effect>[^\n。；;]{1,80})",
            r"由于(?P<cause>[^\n。；;]{1,80})导致(?P<effect>[^\n。；;]{1,80})",
            r"(?P<cause>[^\n。；;]{1,80})因此(?P<effect>[^\n。；;]{1,80})",
            r"(?P<cause>[^\n。；;]{1,80})从而(?P<effect>[^\n。；;]{1,80})",
            r"(?P<cause>[^\n。；;]{1,80})进而(?P<effect>[^\n。；;]{1,80})",
        ]

        out: List[str] = []
        for pat in patterns:
            for m in re.finditer(pat, t):
                cause = (m.group("cause") or "").strip()
                effect = (m.group("effect") or "").strip()
                if not cause or not effect:
                    continue
                s = f"{cause} -> {effect}"
                if s not in out:
                    out.append(s)

        return out[:10]
