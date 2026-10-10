"""R-011: deterministic startup and machine-output ordering.

Every user-facing listing must be emitted in sorted/stable order, repeated
listings must be byte-identical, and ``--json`` machine output must contain
no wall-clock timestamps outside the fields documented as volatile in
``mythic_agent.core.determinism.VOLATILE_JSON_FIELDS``.
"""

import json
import re
from types import SimpleNamespace

from mythic_agent.core.determinism import (
    RANDOMNESS_NOTES,
    VOLATILE_JSON_FIELDS,
    sorted_listing,
    startup_sequence,
)

TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")


# -- listing order ----------------------------------------------------------

def test_providers_sorted_and_stable():
    from mythic_agent.providers.registry import list_providers
    first, second = list_providers(), list_providers()
    assert first == second
    assert first == sorted(first)
    assert first, "expected at least one registered provider"


def test_themes_sorted_and_stable():
    from mythic_agent.ui.themes import list_themes
    first, second = list_themes(), list_themes()
    assert first == second
    assert first == sorted(first)


def test_tool_list_stable():
    from mythic_agent.core.tool_schemas import get_agent_tools

    def names():
        return [t["function"]["name"] for t in get_agent_tools()]

    assert names() == names()
    assert len(names()) > 0


def test_sorted_listing_helper():
    assert sorted_listing(["b", "a", "c"]) == ["a", "b", "c"]
    assert sorted_listing([]) == []


# -- startup sequence recorder ----------------------------------------------

def test_startup_sequence_records_in_order():
    seq = startup_sequence()
    seq.record("logging")
    seq.record("config")
    seq.record("agent", "Primary")
    assert seq.step_names() == ["logging", "config", "agent"]
    assert seq.report() == [
        {"step": "logging", "detail": ""},
        {"step": "config", "detail": ""},
        {"step": "agent", "detail": "Primary"},
    ]


# -- doctor checks -----------------------------------------------------------

def test_doctor_checks_deterministic():
    from mythic_agent.doctor import run_checks
    first = [(r.name, r.status.value, r.message) for r in run_checks()]
    second = [(r.name, r.status.value, r.message) for r in run_checks()]
    assert first == second
    names = [name for name, _, _ in first]
    assert len(names) == len(set(names)), "doctor check names must be unique"


def test_doctor_json_no_undocumented_timestamps(capsys):
    from mythic_agent.doctor import print_results, run_checks
    results = run_checks()
    print_results(results, as_json=True)
    payload = json.loads(capsys.readouterr().out)
    volatile = VOLATILE_JSON_FIELDS["doctor"]
    for entry in payload:
        for key, value in entry.items():
            if key in volatile:
                continue
            assert not TIMESTAMP_RE.search(str(value)), (key, value)


# -- machine output: costs ---------------------------------------------------

def test_costs_json_sorted_stable_and_timestamp_free(tmp_path, capsys):
    from mythic_agent.cli import main
    from mythic_agent.core.costs import CostTracker
    tracker = CostTracker(tmp_path)
    for model in ("zzz-model", "aaa-model", "mmm-model"):
        tracker.record(model, 100, 50)

    def run():
        capsys.readouterr()  # drain
        assert main(["costs", "--workspace", str(tmp_path), "--json"]) == 0
        return capsys.readouterr().out

    first, second = run(), run()
    assert first == second, "costs --json must be byte-identical across runs"
    data = json.loads(first)
    assert list(data["by_model"]) == sorted(data["by_model"])
    assert data["unknown_models"] == sorted(data["unknown_models"])
    assert not TIMESTAMP_RE.search(first)


# -- machine output: cache ---------------------------------------------------

def test_cache_json_stable_and_timestamp_free(tmp_path, capsys, monkeypatch):
    from mythic_agent.cli import main
    from mythic_agent.core import cache as cache_module
    monkeypatch.setattr(cache_module, "default_cache_dir",
                        lambda: tmp_path / "llm-cache")
    assert main(["cache", "--json"]) == 0
    first = capsys.readouterr().out
    assert main(["cache", "--json"]) == 0
    second = capsys.readouterr().out
    assert first == second
    json.loads(first)  # must be valid JSON
    assert not TIMESTAMP_RE.search(first)


# -- machine output: sessions -------------------------------------------------

def test_sessions_json_only_documented_volatile_fields(tmp_path, capsys, monkeypatch):
    from mythic_agent.core import config_manager as cm
    from mythic_agent.terminal import session_command
    monkeypatch.setattr(cm.config_manager, "MYTHIC_DIR", tmp_path / "state")
    monkeypatch.setattr(cm.config_manager, "load_config", lambda: {})
    args = SimpleNamespace(workspace=str(tmp_path), export=None, search=None)
    assert session_command(args) == 0
    first = capsys.readouterr().out
    assert session_command(args) == 0
    second = capsys.readouterr().out
    payload = json.loads(first)
    assert payload["schema_version"] == 1
    assert payload["sessions"] == []
    assert "created_at" in VOLATILE_JSON_FIELDS["sessions"]
    assert "updated_at" in VOLATILE_JSON_FIELDS["sessions"]
    # With no sessions the envelope itself must be fully deterministic.
    assert first == second


# -- randomness is documented, not silent ------------------------------------

def test_randomness_notes_cover_known_nondeterminism():
    assert RANDOMNESS_NOTES, "unseeded randomness must be documented"
    for location, note in RANDOMNESS_NOTES.items():
        assert location and note
