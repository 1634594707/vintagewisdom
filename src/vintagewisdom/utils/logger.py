import logging
import os
from typing import Optional


def get_logger(name: str = "vintagewisdom", level: Optional[str] = None) -> logging.Logger:
    resolved_level = (level or os.getenv("VW_LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return logging.getLogger(name)
