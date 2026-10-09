"""Slice 37 notification tests.

``notify-send`` and the network are never touched: both are stubbed.
"""

import hashlib
import hmac
import json
import subprocess

import pytest

from mythic_agent.core import notifications
from mythic_agent.core.notifications import NotificationError, WebhookSender


def test_notify_uses_notify_send_when_available(monkeypatch):
    calls = []
    monkeypatch.setattr(notifications.shutil, "which", lambda name: "/usr/bin/notify-send")
    monkeypatch.setattr(notifications.subprocess, "run",
                        lambda *a, **k: calls.append((a, k)))
    assert notifications.notify("Done", "Task finished") is True
    (args, kwargs), = calls
    assert args[0] == ["/usr/bin/notify-send", "Done", "Task finished"]
    assert kwargs["check"] is True


def test_notify_falls_back_to_print(monkeypatch, capsys):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)
    assert notifications.notify("Done", "Task finished") is True
    assert "[Done] Task finished" in capsys.readouterr().out


def test_notify_disabled_returns_false(monkeypatch, capsys):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)
    config = {"notifications": {"enabled": False}}
    assert notifications.notify("Done", "x", config) is False
    assert capsys.readouterr().out == ""


def test_notify_desktop_off_returns_false(monkeypatch, capsys):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)
    config = {"notifications": {"desktop": False}}
    assert notifications.notify("Done", "x", config) is False
    assert capsys.readouterr().out == ""


def test_notify_send_failure_raises(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: "/usr/bin/notify-send")

    def boom(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr(notifications.subprocess, "run", boom)
    with pytest.raises(NotificationError):
        notifications.notify("Done", "x")


def test_notify_rejects_empty_title(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)
    with pytest.raises(ValueError):
        notifications.notify("   ", "x")


class _FakeReply:
    status = 200

    def __init__(self, body=b'{"ok": true}'):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_webhook_send_signs_payload(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout=None):
        seen["url"] = request.full_url
        seen["headers"] = dict(request.header_items())
        seen["body"] = request.data
        seen["timeout"] = timeout
        return _FakeReply()

    monkeypatch.setattr(notifications.urllib.request, "urlopen", fake_urlopen)
    sender = WebhookSender(secret="s3cr3t", timeout=5)
    result = sender.send("https://hooks.example.com/mythic", {"event": "done"})
    assert result["status"] == 200
    assert seen["url"] == "https://hooks.example.com/mythic"
    assert seen["timeout"] == 5
    expected = "sha256=" + hmac.new(b"s3cr3t", seen["body"],
                                    hashlib.sha256).hexdigest()
    lowered = {k.lower(): v for k, v in seen["headers"].items()}
    assert lowered["x-mythic-signature"] == expected
    assert json.loads(seen["body"]) == {"event": "done"}


def test_webhook_send_without_secret_omits_signature(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout=None):
        seen["headers"] = dict(request.header_items())
        return _FakeReply()

    monkeypatch.setattr(notifications.urllib.request, "urlopen", fake_urlopen)
    WebhookSender().send("https://hooks.example.com/x", {"a": 1})
    lowered = {k.lower() for k in seen["headers"]}
    assert "x-mythic-signature" not in lowered


def test_webhook_send_rejects_non_http_url():
    with pytest.raises(NotificationError):
        WebhookSender().send("ftp://evil.example/x", {"a": 1})


def test_webhook_send_wraps_transport_errors(monkeypatch):
    def boom(request, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(notifications.urllib.request, "urlopen", boom)
    with pytest.raises(NotificationError) as exc:
        WebhookSender().send("https://hooks.example.com/x", {"a": 1})
    assert "connection refused" in str(exc.value)


def test_notify_all_combines_desktop_and_webhook(monkeypatch):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)

    def fake_urlopen(request, timeout=None):
        return _FakeReply(b"accepted")

    monkeypatch.setattr(notifications.urllib.request, "urlopen", fake_urlopen)
    config = {"notifications": {
        "webhook_url": "https://hooks.example.com/mythic",
        "webhook_secret": "s3cr3t"}}
    result = notifications.notify_all("Done", "All good", config, event="task.done")
    assert result["desktop"] is True
    assert result["webhook"]["status"] == 200
    assert result["webhook"]["body"] == "accepted"


def test_notify_all_survives_dead_webhook(monkeypatch, capsys):
    monkeypatch.setattr(notifications.shutil, "which", lambda name: None)

    def boom(request, timeout=None):
        raise OSError("dns blew up")

    monkeypatch.setattr(notifications.urllib.request, "urlopen", boom)
    config = {"notifications": {"webhook_url": "https://hooks.example.com/x"}}
    result = notifications.notify_all("Done", "All good", config)
    assert result["desktop"] is True
    assert "dns blew up" in result["webhook"]["error"]
    # desktop path still delivered
    assert "[Done] All good" in capsys.readouterr().out
