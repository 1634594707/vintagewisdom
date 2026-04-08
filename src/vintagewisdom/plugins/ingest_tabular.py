from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.ingest_tabular")


class IngestTabularPlugin(Plugin):
    INFO = PluginInfo(
        name="ingest.tabular",
        version="0.1.0",
        description="Normalize tabular dataframes and map to case candidates",
        author="VintageWisdom",
        dependencies=[],
    )

    def initialize(self) -> None:
        try:
            if not hasattr(self.app, "ingest"):
                setattr(self.app, "ingest", {})
            ingest = getattr(self.app, "ingest")
            if isinstance(ingest, dict):
                ingest["tabular"] = self
        except Exception:
            return

    def normalize_dataframe(self, df):
        try:
            import pandas as pd  # type: ignore
        except Exception as e:
            raise RuntimeError("Missing pandas dependency. Install with: pip install -e '.[ingest]'") from e

        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        df = df.copy()
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()
        df = df.replace({"": None})
        df = df.drop_duplicates()
        return df

    def map_to_case_candidates(
        self,
        df,
        *,
        default_domain: str = "",
    ) -> List[Dict[str, Any]]:
        try:
            import pandas as pd  # type: ignore
        except Exception as e:
            raise RuntimeError("Missing pandas dependency. Install with: pip install -e '.[ingest]'") from e

        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        out: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            data = row.to_dict()
            cid = str(data.get("id") or "").strip()
            title = str(data.get("title") or data.get("name") or "").strip()
            domain = str(data.get("domain") or default_domain or "general").strip() or "general"
            if not cid:
                cid = f"case_{abs(hash(title or str(row.name))) % 10**12:012d}"
            if not title:
                title = cid
            out.append(
                {
                    "id": cid,
                    "domain": domain,
                    "title": title,
                    "description": data.get("description"),
                    "decision_node": data.get("decision_node"),
                    "action_taken": data.get("action_taken"),
                    "outcome_result": data.get("outcome_result"),
                    "outcome_timeline": data.get("outcome_timeline"),
                    "lesson_core": data.get("lesson_core"),
                    "confidence": data.get("confidence"),
                }
            )
        return out
