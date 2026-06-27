"""FastAPI application factory and HTTP routes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from loguru import logger

from iau_chatbot.agent.graph import TextLLM, answer_question
from iau_chatbot.agent.state import AgentAnswer
from iau_chatbot.config import Settings
from iau_chatbot.llm import LLMClient

from .errors import ChatbotExecutionError, FeedbackStorageError
from .schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    RuntimeSettingsRequest,
    RuntimeSettingsResponse,
    SessionMessage,
    SessionResponse,
)
from .service import Answerer, ChatbotService, FeedbackStore
from .sessions import SessionStore
from .ui import render_chat_ui

ASSET_DIR = Path(__file__).resolve().parent / "static"


def create_app(
    *,
    settings: Settings | None = None,
    llm: TextLLM | None = None,
    answerer: Answerer | None = None,
) -> FastAPI:
    """Create and configure the chatbot API application."""

    runtime_settings = settings or Settings.from_env()
    runtime_llm = llm or LLMClient(
        api_key=runtime_settings.llm_api_key,
        base_url=runtime_settings.llm_base_url,
        model=runtime_settings.llm_model,
    )
    runtime_answerer = (
        None if answerer else _RuntimeAnswerer(settings=runtime_settings, llm=runtime_llm)
    )
    route_answerer = answerer or runtime_answerer
    sessions = SessionStore()
    chatbot = ChatbotService(
        answerer=route_answerer,
        sessions=sessions,
        timeout_seconds=runtime_settings.chatbot_timeout_seconds,
    )
    feedback_store = FeedbackStore(runtime_settings.feedback_path)
    app = FastAPI(title="IAU QA Chatbot Interface", version="1.0.0")
    app.state.sessions = sessions
    app.state.feedback_store = feedback_store
    app.state.runtime_answerer = runtime_answerer

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def ui() -> str:
        return render_chat_ui()

    @app.get("/assets/logo-uni.png", include_in_schema=False)
    def university_logo() -> FileResponse:
        logo_path = ASSET_DIR / "logo-uni.png"
        if not logo_path.exists():
            raise HTTPException(status_code=404, detail="logo not found")
        return FileResponse(logo_path, media_type="image/png")

    @app.get("/assets/image.png", include_in_schema=False, response_model=None)
    def robot_logo() -> Response:
        image_path = ASSET_DIR / "image.png"
        if image_path.exists():
            return FileResponse(image_path, media_type="image/png")
        return Response(content=_robot_logo_svg(), media_type="image/svg+xml")

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="student-chatbot-interface")

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        question = request.question.strip()
        try:
            result = chatbot.answer(
                question=question,
                session_id=request.session_id,
                metadata=request.metadata,
            )
        except ChatbotExecutionError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.public_detail) from None
        return ChatResponse(
            session_id=result.session_id,
            answer=result.answer,
            sources=result.sources,
            error=None,
        )

    @app.get("/sessions/{session_id}", response_model=SessionResponse)
    def session_history(session_id: str) -> SessionResponse:
        messages = [
            SessionMessage(role=message.role, content=message.content)
            for message in sessions.get_messages(session_id)
        ]
        return SessionResponse(session_id=session_id, messages=messages)

    @app.post("/feedback", response_model=FeedbackResponse)
    def feedback(request: FeedbackRequest) -> FeedbackResponse:
        try:
            feedback_store.append(request)
        except FeedbackStorageError:
            logger.exception("feedback storage failure session_id={}", request.session_id)
            raise HTTPException(status_code=500, detail="feedback could not be stored") from None
        return FeedbackResponse(status="stored")

    @app.post("/settings", response_model=RuntimeSettingsResponse)
    def update_runtime_settings(request: RuntimeSettingsRequest) -> RuntimeSettingsResponse:
        if runtime_answerer is None:
            raise HTTPException(status_code=409, detail="runtime settings are not configurable")
        base_url = request.base_url.strip()
        runtime_answerer.update_llm(api_key=request.llm_api_key.strip(), base_url=base_url)
        logger.info("runtime LLM settings updated base_url={}", base_url)
        return RuntimeSettingsResponse(
            status="updated",
            base_url=base_url,
            llm_model=runtime_settings.llm_model,
        )

    return app


def _agent_answerer(*, settings: Settings, llm: TextLLM) -> Callable[..., AgentAnswer]:
    def answerer(*, question: str, session_id: str | None = None) -> AgentAnswer:
        return answer_question(
            question,
            wiki_dir=settings.wiki_dir,
            llm=llm,
            session_id=session_id,
        )

    return answerer


class _RuntimeAnswerer:
    """Thread-safe answerer whose LLM client can be updated at runtime."""

    def __init__(self, *, settings: Settings, llm: TextLLM) -> None:
        self._settings = settings
        self._llm = llm
        self._lock = Lock()

    def __call__(self, *, question: str, session_id: str | None = None) -> AgentAnswer:
        with self._lock:
            llm = self._llm
        return answer_question(
            question,
            wiki_dir=self._settings.wiki_dir,
            llm=llm,
            session_id=session_id,
        )

    def update_llm(self, *, api_key: str, base_url: str) -> None:
        with self._lock:
            self._llm = LLMClient(
                api_key=api_key,
                base_url=base_url,
                model=self._settings.llm_model,
            )


def _robot_logo_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="Robot logo">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#eff8ff"/>
      <stop offset="100%" stop-color="#d7ebff"/>
    </linearGradient>
    <linearGradient id="body" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#cfe4ff"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="56" fill="url(#bg)"/>
  <circle cx="128" cy="92" r="46" fill="url(#body)" stroke="#2f6fed" stroke-width="8"/>
  <circle cx="112" cy="88" r="8" fill="#0d3f78"/>
  <circle cx="144" cy="88" r="8" fill="#0d3f78"/>
  <path d="M110 108c6 8 30 8 36 0" fill="none" stroke="#0d3f78" stroke-width="7" stroke-linecap="round"/>
  <rect x="74" y="142" width="108" height="72" rx="26" fill="url(#body)" stroke="#2f6fed" stroke-width="8"/>
  <rect x="52" y="160" width="20" height="40" rx="10" fill="#2f6fed"/>
  <rect x="184" y="160" width="20" height="40" rx="10" fill="#2f6fed"/>
  <rect x="108" y="48" width="40" height="18" rx="9" fill="#2f6fed"/>
  <circle cx="128" cy="39" r="10" fill="#2f6fed"/>
  <circle cx="96" cy="168" r="8" fill="#2f6fed"/>
  <circle cx="160" cy="168" r="8" fill="#2f6fed"/>
</svg>"""
