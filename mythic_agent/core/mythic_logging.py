"""Structured JSON logging for Mythic Agent.

Replaces ad-hoc print() calls with structured, level-aware logging.
All log records are JSON objects with timestamp, level, logger name,
message, and optional structured fields.

Usage:
    from mythic_agent.core.mythic_logging import get_logger
    log = get_logger(__name__)
    log.info("agent started", agent="primary", workspace="/path")
    log.error("tool failed", tool="read", error=str(e))

Configure via:
    from mythic_agent.core.mythic_logging import configure
    configure(level="DEBUG", json_output=True, log_file="/path/to/mythic.log")
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_configured = False
_log_file: Path | None = None


class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include structured extras (anything not a standard LogRecord attr)
        standard = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "asctime", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard and not key.startswith("_"):
                try:
                    json.dumps(value)
                    obj[key] = value
                except (TypeError, ValueError):
                    obj[key] = str(value)
        if record.exc_info and record.exc_info[0] is not None:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj)


class TextFormatter(logging.Formatter):
    """Human-readable format for terminal output."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        extras = ""
        standard = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "asctime", "taskName",
        }
        extra_items = [
            f"{k}={v}" for k, v in record.__dict__.items()
            if k not in standard and not k.startswith("_")
        ]
        if extra_items:
            extras = " " + " ".join(extra_items)
        return f"{ts} [{record.levelname}] {record.name}: {record.getMessage()}{extras}"


def configure(
    level: str = "INFO",
    json_output: bool = False,
    log_file: str | Path | None = None,
    force: bool = False,
) -> None:
    """Configure the mythic_agent logger hierarchy.

    Args:
        level: Minimum level (DEBUG, INFO, WARNING, ERROR).
        json_output: If True, console output is JSON; otherwise human-readable.
        log_file: Optional path for a JSON log file (always JSON format).
        force: Reconfigure even if already configured.
    """
    global _configured, _log_file
    if _configured and not force:
        return

    root = logging.getLogger("mythic_agent")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    formatter = JsonFormatter() if json_output else TextFormatter()
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_file:
        _log_file = Path(log_file)
        _log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_log_file, encoding="utf-8")
        file_handler.setFormatter(JsonFormatter())
        root.addHandler(file_handler)

    # Don't propagate to the root logger (avoids duplicate output)
    root.propagate = False
    _configured = True


def get_logger(name: str) -> logging.LoggerAdapter:
    """Get a structured logger for the given module name.

    Returns a LoggerAdapter that accepts keyword arguments as structured fields:
        log.info("turn complete", turns=3, tokens=1500)
    """
    if not _configured:
        configure()
    logger = logging.getLogger(f"mythic_agent.{name}" if not name.startswith("mythic_agent") else name)
    return StructuredAdapter(logger, {})


class StructuredAdapter(logging.LoggerAdapter):
    """LoggerAdapter that merges kwargs into the log record as structured fields."""

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = kwargs.pop("extra", {})
        extra.update(kwargs.pop("fields", {}))
        # Remaining kwargs become structured fields
        extra.update(kwargs)
        kwargs["extra"] = extra
        kwargs["stacklevel"] = kwargs.get("stacklevel", 2)
        return msg, kwargs

    def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        # Route kwargs as structured fields via `extra`, not %-format args
        if args:
            super().log(level, msg, *args, **kwargs)
        else:
            extra = kwargs.pop("extra", {})
            extra.update(kwargs)
            self.logger.log(level, msg, extra=extra,
                            stacklevel=kwargs.pop("stacklevel", 2))
