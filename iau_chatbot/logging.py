"""Logging setup for command-line and API entrypoints."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StdlibLoggerAdapter:
    """Tiny adapter for loguru-style calls when loguru is unavailable."""

    logger: logging.Logger

    def info(self, message: str, *args: Any) -> None:
        self.logger.info(message.format(*args))


def configure_logging(level: str) -> Any:
    """Configure loguru when installed, otherwise stdlib logging."""

    try:
        from loguru import logger
    except ModuleNotFoundError:
        logging.basicConfig(level=getattr(logging, level, logging.INFO))
        return StdlibLoggerAdapter(logging.getLogger("iau_chatbot"))

    logger.remove()
    logger.add(sys.stderr, level=level)
    return logger
