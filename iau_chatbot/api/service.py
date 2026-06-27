"""Service wrapper between HTTP routes and the existing chatbot engine."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
import json
from pathlib import Path
import re
from threading import Lock
import time
from typing import Any, Protocol

from loguru import logger

from iau_chatbot.agent.state import AgentAnswer

from .errors import ChatbotExecutionError, FeedbackStorageError
from .schemas import FeedbackRequest, SourceResponse
from .sessions import SessionStore


class Answerer(Protocol):
    """Callable dependency used by the chat service."""

    def __call__(self, *, question: str, session_id: str | None = None) -> AgentAnswer:
        """Return a grounded answer for a user question."""


@dataclass(frozen=True)
class ChatServiceResult:
    """Normalized chat result returned to HTTP routes."""

    answer: str
    session_id: str
    sources: list[SourceResponse]


class ChatbotService:
    """Thin interface-layer wrapper around the existing chatbot answerer."""

    def __init__(
        self,
        *,
        answerer: Answerer,
        sessions: SessionStore,
        timeout_seconds: float,
    ) -> None:
        self._answerer = answerer
        self._sessions = sessions
        self._timeout_seconds = timeout_seconds

    def answer(
        self,
        *,
        question: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatServiceResult:
        """Call the chatbot core and store the successful conversation turn."""

        resolved_session_id = self._sessions.ensure_session_id(session_id)
        started = time.perf_counter()
        logger.info("chat question received session_id={}", resolved_session_id)
        conversational_answer = _conversational_answer(question)
        if conversational_answer is not None:
            self._sessions.append_turn(
                session_id=resolved_session_id,
                question=question,
                answer=conversational_answer,
            )
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "chat answered conversationally session_id={} elapsed_ms={}",
                resolved_session_id,
                elapsed_ms,
            )
            return ChatServiceResult(
                answer=conversational_answer,
                session_id=resolved_session_id,
                sources=[],
            )
        try:
            result = self._call_answerer(question=question, session_id=resolved_session_id)
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            logger.exception(
                "chat failed session_id={} elapsed_ms={}", resolved_session_id, elapsed_ms
            )
            raise _chatbot_error_from_exception(exc) from exc

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("chat answered session_id={} elapsed_ms={}", resolved_session_id, elapsed_ms)
        answer = result.answer
        self._sessions.append_turn(
            session_id=resolved_session_id,
            question=question,
            answer=answer,
        )
        return ChatServiceResult(
            answer=answer,
            session_id=resolved_session_id,
            sources=[_normalize_source(source) for source in result.sources],
        )

    def _call_answerer(self, *, question: str, session_id: str) -> AgentAnswer:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._answerer, question=question, session_id=session_id)
        try:
            return future.result(timeout=self._timeout_seconds)
        except TimeoutError as exc:
            future.cancel()
            raise ChatbotExecutionError("chatbot timed out") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)


class FeedbackStore:
    """Append-only JSONL feedback storage."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()

    @property
    def path(self) -> Path:
        return self._path

    def append(self, feedback: FeedbackRequest) -> None:
        """Append one feedback record to the configured JSONL file."""

        record = feedback.model_dump()
        record["created_at_unix"] = time.time()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record, ensure_ascii=False, sort_keys=True)
            with self._lock:
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
        except OSError as exc:
            raise FeedbackStorageError("failed to store feedback") from exc


def _normalize_source(source: Any) -> SourceResponse:
    title = _read_attr(source, "title") or _read_attr(source, "name")
    path = (
        _read_attr(source, "path")
        or _read_attr(source, "wiki_page")
        or _read_attr(source, "source_path")
        or _read_attr(source, "source_ref")
    )
    snippet = (
        _read_attr(source, "snippet")
        or _read_attr(source, "excerpt")
        or _read_attr(source, "evidence")
        or _read_attr(source, "summary")
    )
    return SourceResponse(title=str(title or ""), path=str(path or ""), snippet=str(snippet or ""))


def _chatbot_error_from_exception(exc: Exception) -> ChatbotExecutionError:
    message = str(exc)
    if "401" in message or "Unauthorized" in message:
        return ChatbotExecutionError(
            "llm authentication failed",
            public_detail=(
                "خطا در احراز هویت سرویس مدل زبانی. مقدار LLM_API_KEY، "
                "BASE_URL یا LLM_BASE_URL و LLM_MODEL را در فایل .env بررسی کنید."
            ),
            status_code=502,
        )
    return ChatbotExecutionError("chatbot failed to answer")


def _conversational_answer(question: str) -> str | None:
    normalized = _normalize_conversation_text(question)
    greetings = {
        "hello",
        "hi",
        "hey",
        "سلام",
        "درود",
        "salam",
        "سلام خوبی",
        "سلام چطوری",
        "حالت چطوره",
        "خوبی",
        "how are you",
        "how are you doing",
    }
    if normalized in greetings:
        return (
            "سلام، خوش آمدید. من آماده‌ام به پرسش‌های آموزشی و مقررات دانشگاهی شما "
            "پاسخ بدهم. سوالتان را بپرسید تا دقیق و مرحله‌به‌مرحله راهنمایی کنم."
        )
    return None


def _normalize_conversation_text(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("ي", "ی").replace("ك", "ک")
    normalized = re.sub(r"[؟?!.,،؛:]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _read_attr(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)
