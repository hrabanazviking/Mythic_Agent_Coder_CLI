"""Tests for mythic_agent.core.mythic_logging (Slice 12)."""

import io
import json
import logging

import pytest

from mythic_agent.core.mythic_logging import (
    JsonFormatter,
    TextFormatter,
    configure,
    get_logger,
)


@pytest.fixture(autouse=True)
def reset_logging():
    yield
    # Reset so tests don't leak configuration
    root = logging.getLogger("mythic_agent")
    root.handlers.clear()
    import mythic_agent.core.mythic_logging as ml
    ml._configured = False


def test_json_formatter_produces_valid_json():
    fmt = JsonFormatter()
    record = logging.LogRecord(
        name="mythic_agent.test", level=logging.INFO,
        pathname=__file__, lineno=1, msg="hello %s", args=("world",),
        exc_info=None,
    )
    out = fmt.format(record)
    obj = json.loads(out)
    assert obj["message"] == "hello world"
    assert obj["level"] == "INFO"
    assert "timestamp" in obj


def test_json_formatter_includes_structured_fields():
    fmt = JsonFormatter()
    record = logging.LogRecord(
        name="mythic_agent.test", level=logging.WARNING,
        pathname=__file__, lineno=1, msg="careful", args=(),
        exc_info=None,
    )
    record.agent = "primary"
    record.turns = 3
    obj = json.loads(fmt.format(record))
    assert obj["agent"] == "primary"
    assert obj["turns"] == 3


def test_text_formatter_human_readable():
    fmt = TextFormatter()
    record = logging.LogRecord(
        name="mythic_agent.test", level=logging.ERROR,
        pathname=__file__, lineno=1, msg="boom", args=(),
        exc_info=None,
    )
    out = fmt.format(record)
    assert "ERROR" in out
    assert "boom" in out
    assert "{" not in out  # not JSON


def test_get_logger_accepts_kwargs(capsys):
    configure(json_output=True, force=True)
    log = get_logger("slice12")
    log.info("structured", agent="primary", turns=5)
    err = capsys.readouterr().err
    obj = json.loads(err.strip().split("\n")[-1])
    assert obj["agent"] == "primary"
    assert obj["turns"] == 5


def test_configure_idempotent():
    configure(force=True)
    configure()  # should not add duplicate handlers
    root = logging.getLogger("mythic_agent")
    assert len(root.handlers) == 1


def test_log_file_writes_json(tmp_path):
    log_file = tmp_path / "mythic.log"
    configure(json_output=False, log_file=log_file, force=True)
    log = get_logger("filetest")
    log.info("to file", key="value")
    content = log_file.read_text()
    obj = json.loads(content.strip())
    assert obj["message"] == "to file"
    assert obj["key"] == "value"
