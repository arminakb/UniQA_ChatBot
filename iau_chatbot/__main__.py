"""Startup smoke command for the IAU QA chatbot package."""

from __future__ import annotations

import argparse

from . import __version__
from .config import Settings
from .logging import configure_logging


def main() -> int:
    parser = argparse.ArgumentParser(prog="iau-chatbot")
    parser.add_argument("--env-file", default=".env", help="Path to the environment file.")
    args = parser.parse_args()

    settings = Settings.from_env(args.env_file)
    logger = configure_logging(settings.log_level)
    logger.info("IAU-QA-Chatbot v{} configured: {}", __version__, settings.safe_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
