"""Structured logging helpers for CareSense."""

from __future__ import annotations

import logging
from typing import Optional

import structlog


def setup_logging(level: int = logging.INFO) -> None:
    """Configure structlog for JSON + console dual output."""
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Return a structured logger."""
    return structlog.get_logger(name or "caresense")
