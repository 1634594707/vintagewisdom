from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    def __init__(self, config_dir: Path | None = None):
        self._config_dir = config_dir or self._resolve_config_dir()
        self._data: Dict[str, Any] = {}
        self._load()

    def _resolve_config_dir(self) -> Path:
        env_dir = os.getenv("VW_CONFIG_DIR")
        if env_dir:
            return Path(env_dir)
        repo_root = Path(__file__).resolve().parents[3]
        return repo_root / "config"

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {}
        return data

    def _load(self) -> None:
        default_path = self._config_dir / "default.yaml"
        user_path = self._config_dir / "user.yaml"
        default_data = self._load_yaml(default_path)
        user_data = self._load_yaml(user_path)
        self._data = _deep_merge(default_data, user_data)

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".") if key else []
        current: Any = self._data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        parts = key.split(".") if key else []
        current: Any = self._data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        if parts:
            current[parts[-1]] = value
        self._save()

    def _save(self) -> None:
        """保存配置到用户配置文件"""
        user_path = self._config_dir / "user.yaml"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with user_path.open("w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, sort_keys=False)
