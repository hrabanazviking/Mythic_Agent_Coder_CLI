"""Redact configured credentials and common token forms in exports/diagnostics."""

__all__ = [
    "Any",
    "SecretRedactor",
    "protect_logging",
    "redact_text",
]

import logging
import os
import re
import threading
import traceback
from typing import Any

from .secrets_audit import mask_text as _mask_detected_secrets


_sensitive_names = {"api_key", "api_keys", "token", "password", "secret", "authorization"}
_url_auth = re.compile(r"(https?://)[^\s/@]+:[^\s/@]+@")
_url_secret = re.compile(r"([?&](?:api_key|token|key|password)=)[^&#\s]+", re.IGNORECASE)
_known_secrets: set[str] = set()
_secret_lock = threading.RLock()
_factory_installed = False


def _collect(value: Any, sensitive: bool = False) -> set[str]:
    if isinstance(value, dict):
        result = set()
        for key, item in value.items():
            result.update(_collect(item, sensitive or key.lower() in _sensitive_names))
        return result
    if isinstance(value, list):
        return set().union(*(_collect(item, sensitive) for item in value)) if value else set()
    return {value} if sensitive and isinstance(value, str) and value else set()


def redact_text(text: str, secrets: set[str] | None = None) -> str:
    if secrets is None:
        with _secret_lock:
            secrets = set(_known_secrets)
    for secret in sorted(secrets, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    text = _mask_detected_secrets(text)
    return _url_secret.sub(r"\1[REDACTED]", _url_auth.sub(r"\1[REDACTED]@", text))


class SecretRedactor:
    def __init__(self, config: dict[str, Any], *, include_environment: bool = True) -> None:
        self.secrets = _collect(config)
        if include_environment:
            self.secrets.update(value for key, value in os.environ.items()
                                if key.endswith(("_API_KEY", "_TOKEN", "_PASSWORD")) and value)

    def text(self, value: str) -> str:
        return redact_text(value, self.secrets)

    def sanitize(self, value: Any, *, sensitive: bool = False) -> Any:
        if isinstance(value, dict):
            return {key: self.sanitize(item, sensitive=sensitive or key.lower() in _sensitive_names)
                    for key, item in value.items()}
        if isinstance(value, list):
            return [self.sanitize(item, sensitive=sensitive) for item in value]
        if isinstance(value, str):
            return "[REDACTED]" if sensitive and value else self.text(value)
        return value


def protect_logging(redactor: SecretRedactor) -> None:
    """Protect records from every logger, including formatted exception traces."""
    global _factory_installed
    with _secret_lock:
        _known_secrets.update(redactor.secrets)
        if _factory_installed:
            return
        previous_factory = logging.getLogRecordFactory()
        def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = previous_factory(*args, **kwargs)
            record.msg = redact_text(record.getMessage())
            record.args = ()
            if record.exc_info:
                record.exc_text = redact_text("".join(traceback.format_exception(*record.exc_info)))
            return record
        logging.setLogRecordFactory(factory)
        _factory_installed = True
