"""Uvicorn launcher for the chatbot API."""

from __future__ import annotations

import argparse

import uvicorn

from iau_chatbot.config import Settings
from iau_chatbot.llm import LLMClient
from iau_chatbot.logging import configure_logging

from .app import create_app


def main() -> int:
    """Run the FastAPI application with Uvicorn."""

    parser = argparse.ArgumentParser(prog="iau-chatbot-api")
    parser.add_argument("--env-file", default=".env", help="Path to the environment file.")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    args = parser.parse_args()

    settings = Settings.from_env(args.env_file)
    configure_logging(settings.log_level)
    llm = LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
    uvicorn.run(create_app(settings=settings, llm=llm), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
