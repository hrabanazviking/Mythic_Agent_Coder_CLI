"""Desktop notifications and task-completion webhooks (Slice 37).

Config shape (merge into ``config_defaults.yaml``; defaults shown)::

    notifications:
      enabled: true        # master switch
      desktop: true        # try notify-send on Linux, print fallback otherwise
      webhook_url: ''      # POST JSON here when set
      webhook_secret: ''   # HMAC-SHA256 signing secret (optional)

No network traffic happens unless ``webhook_url`` is configured, and no
secrets are ever logged.
"""


from __future__ import annotations

__all__ = [
    "Any",
    "NotificationError",
    "Optional",
    "WebhookSender",
    "notify",
    "notify_all",
]

import hashlib
import hmac
import json
import shutil
import subprocess
import urllib.request
from typing import Any, Optional

from .exceptions import MythicNotificationError

_SIGNATURE_HEADER = "X-Mythic-Signature"


class NotificationError(MythicNotificationError, RuntimeError):
    """A notification or webhook delivery failed."""


def _settings(config: Optional[dict[str, Any]]) -> dict[str, Any]:
    raw = (config or {}).get("notifications", {}) or {}
    return {
        "enabled": raw.get("enabled", True),
        "desktop": raw.get("desktop", True),
        "webhook_url": (raw.get("webhook_url") or "").strip(),
        "webhook_secret": raw.get("webhook_secret") or "",
    }


def notify(title: str, message: str,
           config: Optional[dict[str, Any]] = None) -> bool:
    """Send a desktop notification; print fallback when unavailable.

    Uses ``notify-send`` on Linux when present; otherwise prints
    ``[title] message`` to stdout so headless/CI runs still surface the
    event. Returns True when a notification was dispatched, False when
    notifications are disabled. Raises :class:`NotificationError` only
    when ``notify-send`` itself fails.
    """
    settings = _settings(config)
    if not settings["enabled"] or not settings["desktop"]:
        return False
    if not title.strip():
        raise ValueError("Notification title must not be empty")
    sender = shutil.which("notify-send")
    if sender:
        try:
            subprocess.run([sender, title, message], check=True,
                           capture_output=True, timeout=10)
        except (OSError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired) as exc:
            raise NotificationError(f"notify-send failed: {exc}") from exc
        return True
    print(f"[{title}] {message}")
    return True


class WebhookSender:
    """POST JSON payloads to a webhook URL with optional HMAC signing."""

    def __init__(self, secret: str = "", timeout: float = 10.0) -> None:
        self.secret = secret or ""
        self.timeout = timeout

    def _sign(self, body: bytes) -> Optional[str]:
        if not self.secret:
            return None
        digest = hmac.new(self.secret.encode("utf-8"), body,
                          hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def send(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST ``payload`` as JSON to ``url``.

        Returns ``{"status", "body"}``. When a secret is configured the
        request carries an ``X-Mythic-Signature`` HMAC-SHA256 header so
        receivers can verify authenticity. Raises
        :class:`NotificationError` on transport failures or bad URLs.
        """
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise NotificationError(f"Refusing to POST to non-HTTP(S) URL: {url!r}")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dict")
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        signature = self._sign(body)
        if signature:
            headers[_SIGNATURE_HEADER] = signature
        request = urllib.request.Request(url, data=body, headers=headers,
                                         method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as reply:
                return {"status": reply.status,
                        "body": reply.read().decode("utf-8", "replace")}
        except OSError as exc:
            raise NotificationError(f"Webhook delivery to {url} failed: {exc}") from exc


def notify_all(title: str, message: str,
               config: Optional[dict[str, Any]] = None,
               event: str = "mythic.notification") -> dict[str, Any]:
    """Desktop notification plus configured webhook in one call.

    Returns ``{"desktop": bool, "webhook": dict|None}``. Webhook errors
    are captured as ``{"error": ...}`` so a dead endpoint never breaks
    the desktop path.
    """
    settings = _settings(config)
    desktop = notify(title, message, config)
    webhook_result: Optional[dict[str, Any]] = None
    if settings["enabled"] and settings["webhook_url"]:
        sender = WebhookSender(secret=settings["webhook_secret"])
        payload = {"event": event, "title": title, "message": message}
        try:
            webhook_result = sender.send(settings["webhook_url"], payload)
        except NotificationError as exc:
            webhook_result = {"error": str(exc)}
    return {"desktop": desktop, "webhook": webhook_result}
