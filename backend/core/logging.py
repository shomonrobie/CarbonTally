"""Logging configuration for the CarbonTally Business Processing Engine.

Phase-1 note: the frozen Backend v2.1 coding standards reference ``structlog``
for structured logging, but the core layer is intentionally free of
third-party dependencies (Phase 1 requirement). This module therefore configures
the standard-library :mod:`logging` framework. A structured JSON layer can be
added by ``infra.audit_logger`` in Phase 3 without changing this contract.
"""
from __future__ import annotations

import logging
import sys

_DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a single console handler.

    Idempotent: repeated calls replace the previous handlers rather than
    stacking duplicate output.

    Args:
        level: Root logger threshold (e.g. ``logging.DEBUG``, ``logging.INFO``).
    """
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return the named logger (configured by :func:`configure_logging`).

    Args:
        name: Logger name, conventionally the fully qualified module name.

    Returns:
        A standard-library :class:`logging.Logger`.
    """
    return logging.getLogger(name)
