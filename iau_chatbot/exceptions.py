"""Domain exceptions for the IAU QA chatbot."""


class IAUChatbotError(Exception):
    """Base exception for project-specific failures."""


class ConfigurationError(IAUChatbotError):
    """Raised when required runtime configuration is missing or invalid."""


class IngestionError(IAUChatbotError):
    """Raised when source document ingestion fails."""


class WikiBuildError(IAUChatbotError):
    """Raised when wiki page generation or persistence fails."""
