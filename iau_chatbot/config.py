"""Runtime settings loaded from `.env` files and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .exceptions import ConfigurationError

DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings for the chatbot."""

    llm_api_key: str
    llm_base_url: str
    llm_model: str
    embed_model: str
    pdf_dir: Path
    wiki_dir: Path
    vector_db_path: Path
    log_level: str
    feedback_path: Path = Path("feedback.jsonl")
    chatbot_timeout_seconds: float = 90.0

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> "Settings":
        """Load settings from an optional `.env` file and process environment."""

        path = Path(env_file) if env_file else Path(".env")
        env = dict(os.environ)
        if path.exists():
            env.update(_read_env_file(path))
            base_dir = path.parent.resolve()
        else:
            base_dir = Path.cwd()

        api_key = env.get("LLM_API_KEY", "").strip()
        if not api_key:
            raise ConfigurationError("LLM_API_KEY is required")

        return cls(
            llm_api_key=api_key,
            llm_base_url=_env_value(
                env,
                "LLM_BASE_URL",
                "BASE_URL",
                default=DEFAULT_LLM_BASE_URL,
            ),
            llm_model=_env_value(env, "LLM_MODEL", default=DEFAULT_LLM_MODEL),
            embed_model=_env_value(env, "EMBED_MODEL", default=DEFAULT_EMBED_MODEL),
            pdf_dir=_path(env.get("PDF_DIR", "./raw"), base_dir),
            wiki_dir=_path(env.get("WIKI_DIR", "./wiki"), base_dir),
            vector_db_path=_path(env.get("VECTOR_DB_PATH", "./data/chroma"), base_dir),
            log_level=env.get("LOG_LEVEL", "INFO").strip().upper(),
            feedback_path=_path(env.get("FEEDBACK_PATH", "./feedback.jsonl"), base_dir),
            chatbot_timeout_seconds=float(env.get("CHATBOT_TIMEOUT_SECONDS", "90")),
        )

    def safe_summary(self) -> dict[str, str]:
        """Return log-safe settings without secrets."""

        return {
            "llm_api_key": "***",
            "llm_base_url": self.llm_base_url,
            "llm_model": self.llm_model,
            "embed_model": self.embed_model,
            "pdf_dir": str(self.pdf_dir),
            "wiki_dir": str(self.wiki_dir),
            "vector_db_path": str(self.vector_db_path),
            "log_level": self.log_level,
            "feedback_path": str(self.feedback_path),
            "chatbot_timeout_seconds": str(self.chatbot_timeout_seconds),
        }


def _path(value: str, base_dir: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else base_dir / path


def _env_value(env: Mapping[str, str], *names: str, default: str) -> str:
    for name in names:
        value = env.get(name, "").strip()
        if value:
            return value
    return default


def _read_env_file(path: Path) -> Mapping[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.split("#", 1)[0].strip().strip('"').strip("'")
    return values
