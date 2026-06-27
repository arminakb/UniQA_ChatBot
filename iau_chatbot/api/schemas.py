"""Validated request and response schemas for the chatbot interface."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_QUESTION_LENGTH = 4000


class ChatRequest(BaseModel):
    """Request body for `POST /chat`."""

    question: str = Field(..., max_length=MAX_QUESTION_LENGTH)
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value


class SourceResponse(BaseModel):
    """Normalized source citation returned with an answer."""

    title: str = ""
    path: str = ""
    snippet: str = ""

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Response body for `POST /chat`."""

    answer: str
    session_id: str
    sources: list[SourceResponse] = Field(default_factory=list)
    error: str | None = None


class HealthResponse(BaseModel):
    """Response body for `GET /health`."""

    status: str
    service: str


class SessionMessage(BaseModel):
    """A single message stored in a conversation history."""

    role: str
    content: str


class SessionResponse(BaseModel):
    """Response body for `GET /sessions/{session_id}`."""

    session_id: str
    messages: list[SessionMessage]


class FeedbackRequest(BaseModel):
    """Request body for `POST /feedback`."""

    session_id: str
    question: str
    answer: str
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class FeedbackResponse(BaseModel):
    """Response body for accepted feedback."""

    status: str


class RuntimeSettingsRequest(BaseModel):
    """Request body for updating runtime LLM connection settings."""

    llm_api_key: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)

    @field_validator("llm_api_key", "base_url")
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value


class RuntimeSettingsResponse(BaseModel):
    """Response body for runtime settings updates."""

    status: str
    base_url: str
    llm_model: str
