"""Tests for the FastAPI chatbot interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from iau_chatbot.agent.state import AgentAnswer, AnswerSource
from iau_chatbot.api.app import create_app
from iau_chatbot.api.schemas import ChatRequest, FeedbackRequest, RuntimeSettingsRequest
from iau_chatbot.config import Settings


class FakeLLM:
    """Placeholder LLM dependency; tests inject a fake answerer."""

    def complete_text(self, *, system: str, user: str) -> str:
        raise AssertionError("API tests should call the injected answerer")


def test_health_returns_ok(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path), llm=FakeLLM())
    health = _endpoint(app, "/health")

    response = health()

    assert response.model_dump() == {"status": "ok", "service": "student-chatbot-interface"}


def test_robot_logo_route_returns_asset(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path), llm=FakeLLM())
    robot_logo = _endpoint(app, "/assets/image.png")

    response = robot_logo()

    assert response.media_type in {"image/png", "image/svg+xml"}


def test_chat_returns_agent_answer_with_sources(tmp_path: Path) -> None:
    calls: list[tuple[str, str | None]] = []

    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        calls.append((question, session_id))
        return AgentAnswer(
            answer="دانشجو مجاز به اخذ سقف تعیین‌شده در آیین‌نامه است.",
            session_id=session_id,
            sources=[
                AnswerSource(
                    wiki_page="references/semester-unit-limit.md",
                    title="سقف واحدهای نیمسال",
                    source_ref="raw/Karshenasi.pdf#page=8",
                    excerpt="حداکثر واحدهای قابل اخذ در هر نیمسال.",
                )
            ],
        )

    app = create_app(settings=_settings(tmp_path), llm=FakeLLM(), answerer=answerer)
    chat = _endpoint(app, "/chat")

    response = chat(ChatRequest(question="چند واحد میتونم بردارم؟", session_id="session-1"))

    assert response.model_dump() == {
        "answer": "دانشجو مجاز به اخذ سقف تعیین‌شده در آیین‌نامه است.",
        "session_id": "session-1",
        "sources": [
            {
                "title": "سقف واحدهای نیمسال",
                "path": "references/semester-unit-limit.md",
                "snippet": "حداکثر واحدهای قابل اخذ در هر نیمسال.",
            }
        ],
        "error": None,
    }
    assert calls == [("چند واحد میتونم بردارم؟", "session-1")]


def test_chat_rejects_empty_question() -> None:
    with pytest.raises(ValidationError, match="question must not be empty"):
        ChatRequest(question="  ")


def test_chat_generates_session_id_and_stores_history(tmp_path: Path) -> None:
    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        return AgentAnswer(answer="answer", session_id=session_id, sources=[])

    app = create_app(settings=_settings(tmp_path), llm=FakeLLM(), answerer=answerer)
    chat = _endpoint(app, "/chat")
    session_history = _endpoint(app, "/sessions/{session_id}")

    response = chat(ChatRequest(question="question"))

    session_id = response.session_id
    assert session_id
    history = session_history(session_id)
    assert history.model_dump() == {
        "session_id": session_id,
        "messages": [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ],
    }


def test_chat_returns_friendly_greeting_without_agent_call(tmp_path: Path) -> None:
    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        raise AssertionError("greeting should not call the chatbot core")

    app = create_app(settings=_settings(tmp_path), llm=FakeLLM(), answerer=answerer)
    chat = _endpoint(app, "/chat")

    response = chat(ChatRequest(question="سلام", session_id="session-1"))

    assert "سلام" in response.answer
    assert "پرسش‌های آموزشی" in response.answer
    assert response.session_id == "session-1"
    assert response.sources == []


def test_feedback_stores_feedback(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path), llm=FakeLLM())
    feedback = _endpoint(app, "/feedback")

    response = feedback(
        FeedbackRequest(
            session_id="session-1",
            question="question",
            answer="answer",
            rating=5,
            comment="useful",
        )
    )

    assert response.model_dump() == {"status": "stored"}
    lines = (tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["session_id"] == "session-1"
    assert record["rating"] == 5
    assert record["comment"] == "useful"


def test_feedback_rejects_invalid_rating() -> None:
    with pytest.raises(ValidationError):
        FeedbackRequest(session_id="s", question="q", answer="a", rating=6)


def test_chat_returns_structured_500_for_agent_failures(tmp_path: Path) -> None:
    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        raise RuntimeError("boom")

    app = create_app(settings=_settings(tmp_path), llm=FakeLLM(), answerer=answerer)
    chat = _endpoint(app, "/chat")

    with pytest.raises(HTTPException) as exc_info:
        chat(ChatRequest(question="سقف واحد چقدر است؟"))

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "chatbot failed to answer"


def test_chat_returns_clear_error_for_llm_auth_failures(tmp_path: Path) -> None:
    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        raise RuntimeError("LLM request failed: HTTP Error 401: Unauthorized")

    app = create_app(settings=_settings(tmp_path), llm=FakeLLM(), answerer=answerer)
    chat = _endpoint(app, "/chat")

    with pytest.raises(HTTPException) as exc_info:
        chat(ChatRequest(question="شرایط حذف اضطراری چیست؟"))

    assert exc_info.value.status_code == 502
    assert "LLM_API_KEY" in exc_info.value.detail


def test_runtime_settings_update_returns_non_secret_summary(tmp_path: Path) -> None:
    app = create_app(settings=_settings(tmp_path), llm=FakeLLM())
    update_settings = _endpoint(app, "/settings")

    response = update_settings(
        RuntimeSettingsRequest(
            llm_api_key="new-key",
            base_url="https://openrouter.ai/api/v1",
        )
    )

    assert response.model_dump() == {
        "status": "updated",
        "base_url": "https://openrouter.ai/api/v1",
        "llm_model": "test-model",
    }


def test_runtime_settings_rejects_injected_answerer(tmp_path: Path) -> None:
    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        return AgentAnswer(answer="answer", session_id=session_id, sources=[])

    app = create_app(settings=_settings(tmp_path), llm=FakeLLM(), answerer=answerer)
    update_settings = _endpoint(app, "/settings")

    with pytest.raises(HTTPException) as exc_info:
        update_settings(
            RuntimeSettingsRequest(
                llm_api_key="new-key",
                base_url="https://openrouter.ai/api/v1",
            )
        )

    assert exc_info.value.status_code == 409


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        llm_api_key="test-key",
        llm_base_url="https://llm.example/v1",
        llm_model="test-model",
        embed_model="test-embed",
        pdf_dir=tmp_path / "raw",
        wiki_dir=tmp_path / "wiki",
        vector_db_path=tmp_path / "chroma",
        log_level="INFO",
        feedback_path=tmp_path / "feedback.jsonl",
        chatbot_timeout_seconds=5,
    )


def _endpoint(app: Any, path: str) -> Any:
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")
