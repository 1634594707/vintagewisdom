from __future__ import annotations

import os
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_data_dir(default: Path) -> Path:
    env_dir = os.getenv("VW_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return default
