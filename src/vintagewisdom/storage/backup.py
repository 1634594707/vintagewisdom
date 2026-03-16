from __future__ import annotations

from pathlib import Path


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / db_path.name
    backup_path.write_bytes(db_path.read_bytes())
    return backup_path
