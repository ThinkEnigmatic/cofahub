"""Minimal OpenAI-compatible chat client for local LLM analysis.

Talks to any OpenAI-compatible ``/v1/chat/completions`` endpoint. Defaults to the
machine's local model gateway (``ai-dev llm serve``, loopback 127.0.0.1:8794),
which routes the ``frontend`` model to DeepSeek/BytePlus/Gemini/local per
``routing.yaml`` and holds its own keys — so COFA FORWARD never stores a provider
key. The bearer token is read from ``COFA_LLM_API_KEY`` or the gateway's token
file (0600). If neither is present, the client reports ``available=False`` and the
caller should fall back to deterministic analysis.

LLM output is **untrusted**: callers must treat it as advisory text, never as a
source of truth or an instruction to act on.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_GATEWAY_TOKEN = Path.home() / ".config" / "ai-orchestrator" / "secrets" / "gateway_token"
_DEFAULT_ENDPOINT = "http://127.0.0.1:8794/v1/chat/completions"
_DEFAULT_MODEL = "frontend"

_SYSTEM = (
    "You are an analyst assistant for COFA FORWARD, a weather/climate-intelligence "
    "platform for the Freely Associated States (Palau, FSM, RMI). "
    "Answer using ONLY the provided data snapshot. If the snapshot does not contain "
    "what the user asks, say so explicitly and do not invent numbers, dates, or "
    "probabilities. Quote specific values from the snapshot. Never present an "
    "interpretation as an official forecast or government warning. Be concise."
)


class LLMClient:
    """Chat with an OpenAI-compatible endpoint. Failures never raise."""

    def __init__(self, config=None):
        self.endpoint = _DEFAULT_ENDPOINT
        self.model = _DEFAULT_MODEL
        self.api_key: str | None = None
        if config is not None:
            cfg = config.llm or {}
            self.endpoint = config.env("COFA_LLM_ENDPOINT") or cfg.get("endpoint") or self.endpoint
            self.model = config.env("COFA_LLM_MODEL") or cfg.get("model") or self.model
            key_env = cfg.get("api_key_env") or "COFA_LLM_API_KEY"
            self.api_key = config.env(key_env)
        if not self.api_key and _GATEWAY_TOKEN.is_file():
            try:
                self.api_key = _GATEWAY_TOKEN.read_text(encoding="utf-8").strip() or None
            except OSError:
                self.api_key = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict[str, str]], timeout: float = 90.0) -> dict[str, Any]:
        """Send a chat completion. Returns {ok, text, error, model, backend}."""
        import requests

        if not self.api_key:
            return {"ok": False, "error": "no LLM key configured", "text": ""}
        payload = {"model": self.model, "messages": messages}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return {
                "ok": True,
                "text": text,
                "model": data.get("model", self.model),
                "backend": resp.headers.get("X-Gateway-Backend", ""),
            }
        except requests.RequestException as exc:
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "text": ""}
        except (KeyError, IndexError, ValueError) as exc:
            return {"ok": False, "error": f"bad response: {exc}", "text": ""}

    def analyze(self, context: str, question: str, timeout: float = 90.0) -> dict[str, Any]:
        """Answer one question grounded in a provided data snapshot."""
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"DATA SNAPSHOT:\n{context}\n\nQUESTION:\n{question}"},
        ]
        return self.chat(messages, timeout=timeout)
