"""Backward-compatible imports for API schemas."""

from __future__ import annotations

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
    SourceResponse,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "FeedbackRequest",
    "FeedbackResponse",
    "HealthResponse",
    "RuntimeSettingsRequest",
    "RuntimeSettingsResponse",
    "SessionMessage",
    "SessionResponse",
    "SourceResponse",
]
