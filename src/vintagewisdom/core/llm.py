from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, List, Optional


class LLMService:
    def __init__(
        self,
        *,
        provider: str = "ollama",
        model: str = "qwen3.5:4b",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout_s: int = 30,
        retries: int = 1,
    ) -> None:
        self.provider = (provider or "ollama").lower()
        self.model = model or "qwen3.5:4b"
        self.api_key = api_key or os.getenv("AI_API_KEY", "")
        self.api_base = api_base or os.getenv("AI_API_BASE", "")
        self.timeout_s = int(timeout_s or 30)
        self.retries = max(0, int(retries or 0))

    def check_available(self) -> bool:
        if self.provider == "ollama":
            try:
                req = urllib.request.Request(
                    self._ollama_url("/api/tags"),
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status == 200
            except Exception:
                return False
        if self.provider == "api":
            return bool(self.api_key and self.api_base)
        return False

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict[str, Any]] = None,
        timeout_s: Optional[int] = None,
    ) -> Optional[str]:
        prompt = (prompt or "").strip()
        if not prompt:
            return None

        prompt = _apply_json_schema_prompt(prompt, json_schema)
        timeout = int(timeout_s or self.timeout_s)

        last_err: Optional[Exception] = None
        for _ in range(self.retries + 1):
            try:
                if self.provider == "ollama":
                    return self._ollama_generate(
                        prompt=prompt,
                        model=model or self.model,
                        temperature=temperature,
                        timeout_s=timeout,
                    )
                if self.provider == "api":
                    return self._api_chat(
                        messages=[{"role": "user", "content": prompt}],
                        model=model or self.model,
                        temperature=temperature,
                        timeout_s=timeout,
                    )
                return None
            except Exception as exc:
                last_err = exc
                continue
        return None if last_err is not None else None

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_schema: Optional[Dict[str, Any]] = None,
        timeout_s: Optional[int] = None,
    ) -> Optional[str]:
        if not isinstance(messages, list) or not messages:
            return None

        messages = _apply_json_schema_messages(messages, json_schema)
        timeout = int(timeout_s or self.timeout_s)

        last_err: Optional[Exception] = None
        for _ in range(self.retries + 1):
            try:
                if self.provider == "ollama":
                    return self._ollama_chat(
                        messages=messages,
                        model=model or self.model,
                        temperature=temperature,
                        timeout_s=timeout,
                    )
                if self.provider == "api":
                    return self._api_chat(
                        messages=messages,
                        model=model or self.model,
                        temperature=temperature,
                        timeout_s=timeout,
                    )
                return None
            except Exception as exc:
                last_err = exc
                continue
        return None if last_err is not None else None

    def _ollama_url(self, path: str) -> str:
        base = (self.api_base or "http://localhost:11434").rstrip("/")
        return f"{base}{path}"

    def _ollama_generate(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        timeout_s: int,
    ) -> Optional[str]:
        data = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": float(temperature)},
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self._ollama_url("/api/generate"),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("response") or ""

    def _ollama_chat(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        timeout_s: int,
    ) -> Optional[str]:
        data = json.dumps(
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": float(temperature)},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            self._ollama_url("/api/chat"),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            result = json.loads(response.read().decode("utf-8"))
        msg = result.get("message") if isinstance(result, dict) else {}
        if isinstance(msg, dict):
            return msg.get("content") or ""
        return result.get("response") or ""

    def _api_chat(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        timeout_s: int,
    ) -> Optional[str]:
        if not self.api_key or not self.api_base:
            return None

        data = json.dumps(
            {
                "model": model,
                "messages": messages,
                "temperature": float(temperature),
                "max_tokens": 1000,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{self.api_base.rstrip('/')}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            result = json.loads(response.read().decode("utf-8"))
        choices = result.get("choices") if isinstance(result, dict) else None
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(msg, dict):
                return msg.get("content") or ""
        return ""


def _apply_json_schema_prompt(prompt: str, json_schema: Optional[Dict[str, Any]]) -> str:
    if not json_schema:
        return prompt
    try:
        schema_text = json.dumps(json_schema, ensure_ascii=False)
    except Exception:
        schema_text = str(json_schema)
    return (
        f"{prompt}\n\nReturn ONLY valid JSON that matches this schema:\n{schema_text}\n"
    )


def _apply_json_schema_messages(
    messages: List[Dict[str, str]],
    json_schema: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    if not json_schema:
        return messages
    try:
        schema_text = json.dumps(json_schema, ensure_ascii=False)
    except Exception:
        schema_text = str(json_schema)
    system_hint = (
        "Return ONLY valid JSON that matches this schema:\n" + schema_text
    )
    return [{"role": "system", "content": system_hint}] + list(messages)
