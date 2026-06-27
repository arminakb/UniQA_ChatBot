"""Tests for the OpenAI-compatible LLM client."""

import json
from io import BytesIO
from typing import Any
from urllib.error import URLError

import iau_chatbot.llm as llm_module
from iau_chatbot.llm import LLMClient


def test_llm_client_returns_text_completion(monkeypatch: Any) -> None:
    def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
        assert timeout == 60
        assert request.full_url == "https://llm.example/v1/chat/completions"
        return FakeResponse({"choices": [{"message": {"content": "پاسخ مستند"}}]})

    monkeypatch.setattr(llm_module, "urlopen", fake_urlopen)

    client = LLMClient(api_key="key", base_url="https://llm.example/v1", model="test")

    assert client.complete_text(system="system", user="user") == "پاسخ مستند"


def test_llm_client_retries_json_without_response_format(monkeypatch: Any) -> None:
    seen_payloads: list[dict[str, Any]] = []

    def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
        payload = json.loads(request.data.decode("utf-8"))
        seen_payloads.append(payload)
        if len(seen_payloads) == 1:
            raise URLError("json mode rejected")
        return FakeResponse({"choices": [{"message": {"content": '{"title":"ok"}'}}]})

    monkeypatch.setattr(llm_module, "urlopen", fake_urlopen)

    client = LLMClient(api_key="key", base_url="https://llm.example/v1", model="test", retries=0)

    assert client.complete_json(system="system", user="user") == {"title": "ok"}
    assert seen_payloads[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in seen_payloads[1]


class FakeResponse:
    """Minimal context-manager response for urllib tests."""

    def __init__(self, body: dict[str, Any]) -> None:
        self.body = BytesIO(json.dumps(body).encode("utf-8"))

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def read(self) -> bytes:
        return self.body.read()
