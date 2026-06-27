"""Simple in-memory conversation history for the interface layer."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class SessionMessageRecord:
    """One stored chat message."""

    role: str
    content: str


class SessionStore:
    """Thread-safe in-memory session history.

    This intentionally stays small and dependency-free. It can be replaced by a
    database-backed implementation later without changing route behavior.
    """

    def __init__(self) -> None:
        self._messages: dict[str, list[SessionMessageRecord]] = {}
        self._lock = Lock()

    def ensure_session_id(self, session_id: str | None) -> str:
        """Return the provided session id or create a new one."""

        resolved = session_id.strip() if session_id else ""
        if not resolved:
            resolved = str(uuid4())
        with self._lock:
            self._messages.setdefault(resolved, [])
        return resolved

    def append_turn(self, *, session_id: str, question: str, answer: str) -> None:
        """Store one user/assistant exchange."""

        with self._lock:
            messages = self._messages.setdefault(session_id, [])
            messages.append(SessionMessageRecord(role="user", content=question))
            messages.append(SessionMessageRecord(role="assistant", content=answer))

    def get_messages(self, session_id: str) -> list[SessionMessageRecord]:
        """Return a copy of the stored messages for a session."""

        with self._lock:
            return list(self._messages.get(session_id, []))
