"""Interface-layer exceptions."""

from __future__ import annotations


class ChatbotInterfaceError(Exception):
    """Base class for interface-layer failures."""


class ChatbotExecutionError(ChatbotInterfaceError):
    """Raised when the chatbot core fails or times out."""

    def __init__(
        self,
        message: str,
        *,
        public_detail: str = "chatbot failed to answer",
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.public_detail = public_detail
        self.status_code = status_code


class FeedbackStorageError(ChatbotInterfaceError):
    """Raised when feedback cannot be written."""
