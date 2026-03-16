from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.events import events
from ..nlp.embedder import Embedder
from ..nlp.extractor import Extractor
from ..nlp.classifier import Classifier
from ..nlp.causal import CausalExtractor
from ..utils.logger import get_logger
from .base import Plugin, PluginInfo


log = get_logger("vintagewisdom.plugins.nlp_basic")


class NLPBasicPlugin(Plugin):
    INFO = PluginInfo(
        name="nlp.basic",
        version="0.1.0",
        description="Basic NLP utilities (embedder/entity extractor/intent/causal)",
        author="VintageWisdom",
        dependencies=[],
    )

    def __init__(self, app: Any, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(app, config)

    def initialize(self) -> None:
        try:
            self.app.nlp = {
                "embedder": Embedder(),
                "extractor": Extractor(),
                "classifier": Classifier(),
                "causal": CausalExtractor(),
            }
        except Exception as e:
            log.error("nlp.basic init failed: %s", e)
            return
        events.emit("nlp.ready", {"name": "basic"})
