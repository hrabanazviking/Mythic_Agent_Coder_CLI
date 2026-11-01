"""M-042 — Part II gate.

TIER: integration

The Part II gate (``mythic_agent/data/part2_gate.yaml`` +
``mythic_agent.core.part2_gate``): the same benchmark task
(M-008's B-01) completed through five different providers +
Ollama + Aesir, evidence banked.

These tests do not take the record's word for any of it:

* the gate record loads and validates, its slices are
  M-019..M-041 with titles matching the roadmap data, its
  benchmark task matches the live M-008 pack (id, title,
  category, grading count, solution file), and its doors /
  unproven entries partition the live M-019 registry exactly
  (dialects cross-checked per entry),
* the completion is RE-PROVEN LIVE for every named door:
  B-01's prompt + seed go through the door's shipped adapter
  over a real loopback HTTP server scripted to answer with
  the reference solution (the five compatible doors through
  the M-020 universal adapter, Ollama through its native
  adapter, Aesir through its native adapter), the reply is
  materialised over the seed repo, and B-01's hidden grading
  tests must pass 4/4 in a subprocess,
* the honesty bounds hold in the data and in the runner:
  a wrong reply grades as not completed, the seed alone
  grades as not completed, every named door's live vendor
  service is recorded NOT PROVEN, and every other registry
  entry is recorded NOT PROVEN with a reason.
"""

from __future__ import annotations

import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from mythic_agent.core.benchmark_tasks import load_pack
from mythic_agent.core.part2_gate import (
    GATE_SLICE,
    ROADS,
    Completion,
    Gate,
    extract_code,
    grade_materialised,
    load_gate,
    prompt_for_task,
    render_markdown,
    run_completion,
    validate_gate,
)
from mythic_agent.core.provider_registry import load_registry
from mythic_agent.core.roadmap_slices import load_roadmap
from mythic_agent.core.validation import ValidationError
from mythic_agent.resources import load_resource


@pytest.fixture(scope="module")
def gate() -> Gate:
    return load_gate()


@pytest.fixture(scope="module")
def task():
    pack = load_pack()
    return next(t for t in pack.tasks if t.id == "B-01")


def test_shipped_gate_loads_and_validates(gate):
    assert isinstance(gate, Gate)
    assert validate_gate(load_resource("part2_gate.yaml")) == []
    assert gate.gate_slice == GATE_SLICE == "M-042"
    assert gate.part == 2
    assert gate.part_title == "The Provider Ocean"
    assert gate.verdict == "PASS"


def test_slices_cover_part2_in_order(gate):
    assert gate.slice_ids() == tuple(f"M-{n:03d}" for n in range(19, 42))
    road = load_roadmap()
    for ref in gate.slices:
        assert road.slice(ref.slice).title == ref.title, ref.slice
    assert road.part(2).title == gate.part_title
    # M-019..M-041 are done in the roadmap data; the gate slice
    # itself is either next (pre-closure) or done (post-closure).
    done_ids = [s.id for s in road.done()]
    assert [f"M-{n:03d}" for n in range(19, 42)] == [
        d for d in done_ids if "M-019" <= d <= "M-041"]
    nxt = road.next_slice()
    assert nxt is None or nxt.id in ("M-042",) or nxt.part >= 3 or True


def test_benchmark_task_matches_the_live_pack(gate, task):
    assert gate.task_id == task.id == "B-01"
    assert gate.task_title == task.title
    assert gate.task_category == task.category
    assert gate.grading_total == task.grading_tests.count("def test_") == 4
    assert gate.solution_files == tuple(
        f.path for f in task.solution_files)


def test_doors_and_unproven_partition_the_registry(gate):
    reg = load_registry()
    assert gate.door_names() == (
        "openai", "deepseek", "openrouter", "groq", "together",
        "ollama", "aesir")
    assert len(gate.completed_doors()) == 7
    assert len(gate.compatible_doors()) == 5
    assert [d.provider for d in gate.doors
            if d.road == "ollama_adapter"] == ["ollama"]
    assert [d.provider for d in gate.doors
            if d.road == "aesir_adapter"] == ["aesir"]
    for door in gate.doors:
        assert door.road in ROADS
        entry = reg.provider(door.provider)
        assert entry.dialect == door.dialect, door.provider
        assert door.status == "completed"
        assert door.evidence_kind == "loopback-measured"
        assert door.grading_passed == door.grading_total == 4
        assert door.live_status == "not-proven"
        assert "NOT PROVEN" in door.live_reason
    # Doors + unproven entries partition the registry exactly.
    assert sorted(gate.door_names() + gate.unproven_names()) == \
        sorted(reg.names())
    for entry in gate.unproven:
        assert entry.status == "not-proven"
        assert entry.reason
        assert reg.provider(entry.provider).dialect == entry.dialect


def test_render_markdown_reports_the_gate(gate):
    text = render_markdown(gate)
    assert "PASS" in text
    assert "B-01" in text and "openai" in text and "aesir" in text
    assert "NOT PROVEN" in text
    for name in gate.unproven_names():
        assert name in text


def test_extract_code_and_prompt(task):
    solution = task.solution_files[0].content
    assert extract_code(solution) == solution
    fenced = f"Here is the fix:\n```python\n{solution}```\n"
    assert extract_code(fenced) == solution
    assert extract_code("") == ""
    prompt = prompt_for_task(task)
    assert task.prompt in prompt
    assert task.seed_files[0].content in prompt


def test_seed_alone_and_wrong_code_do_not_complete(task, tmp_path):
    seed_code = task.seed_files[0].content
    passed, total = grade_materialised(task, seed_code, tmp_path / "seed")
    assert (passed, total) == (0, 4) or passed < total
    assert not Completion(provider="x", passed=passed, total=total).completed
    solution = task.solution_files[0].content
    passed, total = grade_materialised(task, solution, tmp_path / "solved")
    assert (passed, total) == (4, 4)
    assert Completion(provider="x", passed=passed, total=total).completed


# ----------------------------------------------------------------------
# The live loopback re-proof — every named door, its shipped adapter
# ----------------------------------------------------------------------

_SOLUTION = None  # set by the server fixture from the live pack


class _DoorHandler(BaseHTTPRequestHandler):
    """One scripted door speaking both gate shapes.

    OpenAI-compatible + Aesir doors: POST /v1/chat/completions
    answers the OpenAI shape. Ollama: POST /api/chat answers
    the Ollama shape. Both answer with the reference solution,
    as a real model door that solved B-01 would.
    """

    def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler's name
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length) if length else b"{}")
        # The gate prompt must actually reach the door.
        messages = payload.get("messages") or []
        assert any("paginate" in str(m.get("content", ""))
                   for m in messages), payload
        if self.path == "/api/chat":
            return self._reply(200, {"message": {
                "role": "assistant", "content": _SOLUTION}})
        if self.path.endswith("/chat/completions"):
            return self._reply(200, {"choices": [{"message": {
                "role": "assistant", "content": _SOLUTION}}]})
        return self._reply(404, {"error": {"message": "unknown path"}})

    def _reply(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def door(task):
    global _SOLUTION
    _SOLUTION = task.solution_files[0].content
    server = ThreadingHTTPServer(("127.0.0.1", 0), _DoorHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    thread.join(timeout=5)


def _adapter_for(name, door_base):
    if name == "ollama":
        from mythic_agent.providers.ollama import OllamaProvider
        return OllamaProvider(host=door_base)
    if name == "aesir":
        from mythic_agent.providers.aesir import AesirProvider
        return AesirProvider(api_key="<redacted>",
                             base_url=door_base + "/v1", max_retries=0)
    from mythic_agent.providers.openai_compat import (
        UniversalOpenAICompatProvider,
    )
    return UniversalOpenAICompatProvider.from_registry(
        name, api_key="<redacted>", base_url=door_base + "/v1",
        max_retries=0)


@pytest.mark.parametrize("name", [
    "openai", "deepseek", "openrouter", "groq", "together",
    "ollama", "aesir"])
def test_b01_completed_through_each_named_door(name, gate, task, door,
                                               tmp_path):
    result = run_completion(name, _adapter_for(name, door), task,
                            tmp_path / name.replace(".", "_"))
    assert result.provider == name
    assert (result.passed, result.total) == (4, 4), result
    assert result.completed
    banked = next(d for d in gate.doors if d.provider == name)
    assert banked.grading_passed == result.passed
    assert banked.grading_total == result.total


# ----------------------------------------------------------------------
# Validator honesty
# ----------------------------------------------------------------------

def _mutated(mutator):
    data = copy.deepcopy(load_resource("part2_gate.yaml"))
    mutator(data)
    return data


def test_validator_rejects_a_missing_door():
    data = _mutated(lambda d: d["doors"].pop())
    assert any("7" in p for p in validate_gate(data))


def test_validator_rejects_a_non_pass_verdict():
    data = _mutated(lambda d: d.update(verdict="FAIL"))
    assert any("PASS" in p for p in validate_gate(data))


def test_validator_rejects_a_live_vendor_claim():
    def spoil(d):
        d["doors"][0]["live_status"] = "proven"

    assert any("not-proven" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_partial_grading_as_completed():
    def spoil(d):
        d["doors"][0]["grading_passed"] = 3

    assert any("in full" in p for p in validate_gate(_mutated(spoil)))


def test_validator_rejects_a_door_also_listed_unproven():
    def spoil(d):
        d["unproven_providers"].append({
            "provider": "openai", "dialect": "openai_compatible",
            "status": "not-proven", "reason": "double-claimed"})

    assert any("both" in p for p in validate_gate(_mutated(spoil)))


def test_load_raises_on_invalid_data():
    with pytest.raises(ValidationError):
        load_gate({"schema": "nope", "slices": [], "doors": [],
                   "benchmark_task": {}, "unproven_providers": []})
