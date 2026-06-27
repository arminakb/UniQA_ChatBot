"""Small OpenAI-compatible chat client for wiki and answer generation."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .exceptions import WikiBuildError


class LLMClient:
    """Call an OpenAI-compatible chat completions API."""

    def __init__(self, *, api_key: str, base_url: str, model: str, retries: int = 2) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.retries = retries

    def complete_text(self, *, system: str, user: str) -> str:
        """Return text from a chat completion response."""

        content = self._complete(system=system, user=user)
        if not isinstance(content, str) or not content.strip():
            raise WikiBuildError("LLM returned empty text")
        return content

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        """Return a JSON object from a chat completion response."""

        try:
            content = self._complete(system=system, user=user, json_mode=True)
        except WikiBuildError:
            content = self._complete(system=system, user=user)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise WikiBuildError(f"LLM returned invalid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise WikiBuildError("LLM returned JSON that is not an object")
        return parsed

    def _complete(self, *, system: str, user: str, json_mode: bool = False) -> str:
        """Call the configured OpenAI-compatible chat endpoint."""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        data = json.dumps(payload).encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            request = Request(
                f"{self.base_url}/chat/completions",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=60) as response:
                    body = json.loads(response.read().decode("utf-8"))
                return str(body["choices"][0]["message"]["content"])
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.25 * (attempt + 1))
                    continue
        raise WikiBuildError(f"LLM request failed: {last_error}") from last_error
