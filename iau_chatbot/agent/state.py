"""State and result types for the Phase 5 QA agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

from iau_chatbot.retrieval.lexical import RetrievedPage


@dataclass(frozen=True)
class AnswerSource:
    """A cited source attached to an answer."""

    wiki_page: str
    title: str
    source_ref: str
    excerpt: str


@dataclass(frozen=True)
class AgentAnswer:
    """Public answer returned by the QA agent."""

    answer: str
    sources: list[AnswerSource]
    session_id: str | None = None
    errors: list[str] = field(default_factory=list)


class AgentState(TypedDict, total=False):
    """LangGraph state for grounded question answering."""

    question: str
    session_id: str | None
    retrieved_pages: list[RetrievedPage]
    context: str
    answer: str
    sources: list[AnswerSource]
    errors: list[str]
