"""M-259 Platform matrix final - pure-layer tests.

TIER: unit

M-013's table re-proven cell by cell; unproven
cells ship labelled NOT PROVEN, not silent: a
cell counts PROVEN only on evidence measured
locally, and an unproven cell with nothing
recorded stands open as silent.
"""
import pytest

from mythic_agent.core.platform_matrix_final import (
    BARE_CLAIMS,
    CELLS,
    EVIDENCE_KINDS,
    HELD_EVIDENCE,
    PLATFORMS,
    STAGES,
    CellEntry,
    CellRegistry,
    MatrixRecord,
    default_registry,
    derive_standing,
    derive_verdict,
    format_cell,
    format_cells,
    format_record,
    format_records,
    prepare_report,
)
from mythic_agent.core.validation import ValidationError


def fresh_record(**kw):
    base = dict(cell="P-01",
                run="matrix-2026-11-a",
                date="2026-11-13", verdict="PROVEN",
                proof_kind="local-measured",
                stages=STAGES,
                claims=("local_run_ref", "report_ref"))
    base.update(kw)
    return MatrixRecord(**base)


def not_proven_record(**kw):
    base = dict(cell="P-08",
                run="matrix-2026-11-a",
                date="2026-11-13", verdict="NOT PROVEN",
                proof_kind="none",
                stages=STAGES,
                claims=("report_ref",))
    base.update(kw)
    return MatrixRecord(**base)


def full_book(**overrides):
    records = []
    for cell_id in default_registry().combinations():
        if cell_id in ("P-01", "P-02", "P-03"):
            kw = dict(cell=cell_id, run="matrix-2026-11-a",
                      date="2026-11-13", verdict="PROVEN",
                      proof_kind="local-measured",
                      stages=STAGES,
                      claims=("local_run_ref", "report_ref"))
        else:
            kw = dict(cell=cell_id, run="matrix-2026-11-a",
                      date="2026-11-13", verdict="NOT PROVEN",
                      proof_kind="historical-only",
                      stages=STAGES,
                      claims=("report_ref",))
        kw.update(overrides.get(cell_id, {}))
        records.append(MatrixRecord(**kw))
    return records


def test_registry_holds_twelve_cells_listed_only():
    reg = default_registry()
    assert len(reg.ids()) == 12
    assert reg.ids()[0] == "P-01"
    assert reg.ids()[-1] == "P-12"
    assert all(e.standing == "listed" for e in reg.entries())
    assert len(reg.combinations()) == 12


def test_registry_cells_cover_every_platform_surface():
    reg = default_registry()
    pairs = {(e.platform, e.surface) for e in reg.entries()}
    assert len(pairs) == 12
    assert reg.get("P-01").platform == "linux"
    assert reg.get("P-01").surface == "install"
    assert reg.get("P-12").platform == "macos"
    assert reg.get("P-12").surface == "voice"
    assert PLATFORMS == ("linux", "windows", "macos")


def test_registry_unknown_cell_refused_by_name():
    with pytest.raises(ValidationError, match="unknown cell: P-99"):
        default_registry().get("P-99")


def test_registry_duplicate_refused():
    with pytest.raises(ValidationError, match="duplicate cell"):
        CellRegistry(CELLS + CELLS[:1])


def test_entry_half_written_refused():
    with pytest.raises(ValidationError, match="missing reason"):
        CellRegistry([CellEntry("P-01", "linux", "install", "listed", "")])


def test_entry_published_standing_refused():
    with pytest.raises(ValidationError, match="listed data only"):
        CellRegistry([CellEntry("P-01", "linux", "install", "published", "why")])


def test_entry_unknown_platform_refused():
    with pytest.raises(ValidationError, match="unknown cell platform"):
        CellRegistry([CellEntry("P-01", "amiga", "install", "listed", "why")])


def test_record_proven_local_measured_stands_held():
    standing = derive_standing(fresh_record())
    assert standing.held
    assert standing.grade == "held"
    assert standing.gaps == ()


def test_record_incomplete_walk_stands_open():
    standing = derive_standing(fresh_record(stages=STAGES[:3]))
    assert not standing.held
    assert any("not held" in g for g in standing.gaps)


def test_record_bad_stage_step_stands_open():
    bad = ("named", "judged", "labelled", "held")
    standing = derive_standing(fresh_record(stages=bad))
    assert not standing.held
    assert any("not in the walk" in g for g in standing.gaps)


def test_record_proven_on_historical_evidence_stands_open():
    standing = derive_standing(fresh_record(proof_kind="historical-only"))
    assert not standing.held
    assert any("no inheritance" in g for g in standing.gaps)


def test_record_proven_without_local_evidence_stands_open():
    standing = derive_standing(fresh_record(claims=("report_ref",)))
    assert not standing.held
    assert any("no held local evidence" in g for g in standing.gaps)


def test_record_proven_on_bare_claims_stands_open():
    standing = derive_standing(fresh_record(claims=("feeling",)))
    assert not standing.held
    assert any("bare claims only" in g for g in standing.gaps)


def test_record_not_proven_labelled_stands_held():
    standing = derive_standing(not_proven_record())
    assert standing.held
    assert standing.grade == "held"


def test_record_not_proven_silent_stands_open():
    standing = derive_standing(not_proven_record(claims=()))
    assert not standing.held
    assert any("silent" in g for g in standing.gaps)


def test_record_without_date_stands_open():
    standing = derive_standing(fresh_record(date=""))
    assert not standing.held
    assert any("no re-proof date" in g for g in standing.gaps)


def test_record_unknown_verdict_refused():
    with pytest.raises(ValidationError, match="unknown record verdict"):
        derive_standing(fresh_record(verdict="MAYBE"))


def test_verdict_full_book_ready_with_labelled_cells():
    verdict = derive_verdict(full_book())
    assert verdict.ready
    assert verdict.gaps == ()
    assert verdict.proven_cells == ("P-01", "P-02", "P-03")
    assert len(verdict.not_proven_cells) == 9
    assert verdict.missing_cells == ()


def test_verdict_missing_cell_stops_the_matrix():
    verdict = derive_verdict(full_book()[:-1])
    assert not verdict.ready
    assert verdict.missing_cells == ("P-12",)
    assert any("P-12" in g for g in verdict.gaps)


def test_verdict_open_record_stops_the_matrix():
    verdict = derive_verdict(full_book(**{"P-02": {"proof_kind": "none"}}))
    assert not verdict.ready
    assert any("P-02 stands open" in g for g in verdict.gaps)


def test_verdict_duplicate_cell_named():
    records = full_book()
    records.append(records[0])
    verdict = derive_verdict(records)
    assert not verdict.ready
    assert any("two re-proofs" in g for g in verdict.gaps)


def test_report_ready_and_shared_states():
    report = prepare_report("matrix-a", "P-01", "cells as re-proven",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",))
    assert report.state == "ready"
    shared = prepare_report("matrix-a", "P-01", "cells as re-proven",
                            "2026-11-13", 3, 9, 12,
                            claims=("local_run_ref",), state="shared",
                            certified=True)
    assert shared.state == "shared"
    assert shared.certified


def test_report_sealed_state_refused():
    with pytest.raises(ValidationError, match="ready or shared only"):
        prepare_report("matrix-a", "P-01", "cells", "2026-11-13",
                       3, 9, 12, claims=("local_run_ref",), state="sealed")


def test_report_certified_short_of_answered_refused():
    with pytest.raises(ValidationError, match="matrix final"):
        prepare_report("matrix-a", "P-01", "cells", "2026-11-13",
                       3, 5, 12, claims=("local_run_ref",), certified=True)


def test_report_bare_claim_refused_and_format_roads():
    with pytest.raises(ValidationError, match="bare claim"):
        prepare_report("matrix-a", "P-01", "cells", "2026-11-13",
                       3, 9, 12, claims=("feeling",))
    assert "P-01" in format_cell(default_registry().get("P-01"))
    assert "P-12" in format_cells()
    assert "PROVEN" in format_record(fresh_record())
    assert "NOT PROVEN" in format_records([not_proven_record()])
    assert set(HELD_EVIDENCE) <= set(EVIDENCE_KINDS)
    assert set(BARE_CLAIMS) <= set(EVIDENCE_KINDS)
# ---------------------------------------------------------------------
# M-259 Platform matrix final - agent layer. The pure book is held
# by a session registry in the agent layer alone: cells are read
# from the shipped registry, matrix records are held one by one for
# the session, records, viewed standings and held reports are
# published as session news through the checkpoint road
# (journal-first, deduped per record, standing and verdict),
# standings, the index and the verdict are derived at call time from
# the held records - a cell stands held only when it rests on held
# proof evidence and stands answered - matrix reports are held only
# as reports, state ready by default, may be marked shared by a
# human, a certification claimed only when every cell stands
# answered, and never inflated, and the registry is session state,
# never a stored setting. This layer runs nothing, installs nothing
# and probes no network.
# ---------------------------------------------------------------------

from pathlib import Path as _Path

from mythic_agent.agents.llm import (
    PLATFORMMATRIXFINAL_USAGE,
    parse_platformmatrixfinal_args,
)
from mythic_agent.core.sessions import SessionStore as _SessionStore
from mythic_agent.core.platform_matrix_final import (
    PLAIN_EXPLANATION,
    PLATFORM_MATRIX_FINAL_SCHEMA,
)

ROOT = _Path(__file__).resolve().parent.parent

_PM_EVENT_TYPES = (
    "platformmatrixfinal_record", "platformmatrixfinal_standing",
    "platformmatrixfinal_verdict")

ALL_CELLS = ["P-01", "P-02", "P-03", "P-04", "P-05", "P-06",
             "P-07", "P-08", "P-09", "P-10", "P-11", "P-12"]


def _pm_records(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _pm_record(**overrides):
    raw = {
        "cell": "P-01",
        "run": "reproof-2026-11-a",
        "date": "2026-11-13",
        "verdict": "PROVEN",
        "proof_kind": "local-measured",
        "stages": list(STAGES),
        "claims": ["local_run_ref", "journal_ref"],
    }
    raw.update(overrides)
    return raw


def _pm_fresh_for(cell, run="reproof-2026-11-a"):
    return _pm_record(cell=cell, run=run)


class TestPlatformMatrixFinalAgentStatus:
    def test_status_starts_unheld_but_shows_the_shipped_cells(
            self, agent):
        status = agent.platformmatrixfinal_status()
        assert status["records"] == []
        assert status["book"] is None
        assert status["platformmatrixfinal_book"]["schema"] == (
            PLATFORM_MATRIX_FINAL_SCHEMA)
        assert [c["id"] for c in status[
            "platformmatrixfinal_book"]["cells"]] == ALL_CELLS
        assert status["platformmatrixfinal_book"]["records"] == []
        assert status["platformmatrixfinal_book"]["reports"] == []
        assert status["held"] == []
        assert status["open"] == []
        assert status["index"]["gaps"] == []
        assert status["index"]["total"] == 0
        assert status["verdict"]["verdict"] == "open"
        assert status["records_text"] == ""
        assert "P-01" in status["cells_text"]
        assert "standing listed" in status["cells_text"]
        assert "none recorded this session" in status["screen"]
        assert "platform matrix" in status["plain_words"]
        assert status["explanation"] == PLAIN_EXPLANATION
        assert status["usage"] == PLATFORMMATRIXFINAL_USAGE

    def test_registry_is_one_per_agent(self, agent):
        first = agent._platformmatrixfinal_registry()
        assert agent._platformmatrixfinal_registry() is first
        assert agent._platformmatrixfinal_store is first
        for name in ("platformmatrixfinal_cells",
                     "platformmatrixfinal_book",
                     "platformmatrixfinal_status",
                     "get_platformmatrixfinal_cell",
                     "get_platformmatrixfinal_record",
                     "platformmatrixfinal_standing",
                     "records_for_verdict",
                     "platformmatrixfinal_held",
                     "platformmatrixfinal_index",
                     "platformmatrixfinal_verdict",
                     "prepare_platformmatrixfinal_report",
                     "get_platformmatrixfinal_report",
                     "platformmatrixfinal_reports",
                     "report_platformmatrixfinal"):
            assert callable(getattr(agent, name))
        assert not (set(vars(agent)) & {
            "_platformmatrixfinal_registry",
            "platformmatrixfinal_cells",
            "platformmatrixfinal_book",
            "platformmatrixfinal_status",
            "get_platformmatrixfinal_cell",
            "get_platformmatrixfinal_record",
            "platformmatrixfinal_standing", "records_for_verdict",
            "platformmatrixfinal_held", "platformmatrixfinal_index",
            "platformmatrixfinal_verdict",
            "register_platformmatrixfinal_record",
            "register_platformmatrixfinal_records",
            "record_platformmatrixfinal_records",
            "view_platformmatrixfinal",
            "prepare_platformmatrixfinal_report",
            "get_platformmatrixfinal_report",
            "platformmatrixfinal_reports",
            "report_platformmatrixfinal",
            "_publish_platformmatrixfinal_record",
            "_platformmatrixfinal_screen",
            "_platformmatrixfinal_effective_record"})

    def test_reads_register_and_publish_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.platformmatrixfinal_status()
        entry = agent.get_platformmatrixfinal_cell("P-01")
        assert entry.platform == "linux"
        assert entry.surface == "install"
        standing = agent.platformmatrixfinal_standing("P-01")
        assert standing.held is False
        assert standing.stage == "unseen"
        assert standing.grade == "open"
        assert agent.platformmatrixfinal_held() == []
        assert agent.records_for_verdict("PROVEN") == []
        agent.platformmatrixfinal_index()
        agent.platformmatrixfinal_verdict()
        agent.report_platformmatrixfinal()
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PM_EVENT_TYPES] == []
        with pytest.raises(ValueError, match="unknown cell"):
            agent.get_platformmatrixfinal_cell("guess")
        with pytest.raises(ValueError, match="unknown cell"):
            agent.platformmatrixfinal_standing("guess")
        with pytest.raises(ValueError, match="holds no"):
            agent.get_platformmatrixfinal_record("P-01")
        with pytest.raises(ValueError):
            agent.records_for_verdict("")
        agent.close()


class TestPlatformMatrixFinalAgentHolding:
    def test_register_record_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_platformmatrixfinal_record(
            _pm_record())
        assert result["record"]["cell"] == "P-01"
        assert result["record_news"]["type"] == (
            "platformmatrixfinal_record")
        assert "held as answered" in result["screen"]
        status = agent.platformmatrixfinal_status()
        assert [r["cell"] for r in status["records"]] == [
            "P-01"]
        assert status["book"]["records"][0]["run"] == (
            "reproof-2026-11-a")
        assert status["held"] == ["P-01"]
        assert status["open"] == []
        assert "held as answered" in status["records_text"]
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_record")) == 1
        agent.close()

    def test_duplicate_record_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_platformmatrixfinal_record(_pm_record())
        with pytest.raises(ValueError, match="P-01"):
            agent.register_platformmatrixfinal_record(
                _pm_record(run="reproof-2026-11-b"))
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_record")) == 1
        agent.close()

    def test_register_record_refuses_unknown_claim_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError,
                           match="evidence kind"):
            agent.register_platformmatrixfinal_record(
                _pm_record(claims=["vibes"]))
        assert agent.platformmatrixfinal_status()["records"] == []
        assert _pm_records(
            store, session_id, "platformmatrixfinal_record") == []
        agent.close()

    def test_register_records_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.register_platformmatrixfinal_records([
            _pm_fresh_for("P-05"), _pm_record()])
        assert result["count"] == 2
        assert [r["cell"] for r in result["records_news"]] == [
            "P-05", "P-01"]
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_record")) == 2
        agent.close()

    def test_record_records_boards_a_set_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.record_platformmatrixfinal_records(
            [_pm_fresh_for("P-05")])
        assert result["count"] == 1
        assert result["book"]["schema"] == (
            PLATFORM_MATRIX_FINAL_SCHEMA)
        with pytest.raises(ValueError, match="already boarded"):
            agent.record_platformmatrixfinal_records(
                [_pm_fresh_for("P-05")])
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_record")) == 1
        agent.close()

    def test_view_record_derives_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_platformmatrixfinal_record(_pm_record())
        result = agent.view_platformmatrixfinal("P-01")
        assert result["cell"]["id"] == "P-01"
        assert result["standing"]["held"] is True
        assert result["record"]["run"] == "reproof-2026-11-a"
        assert result["record_news"]["type"] == (
            "platformmatrixfinal_standing")
        assert result["held_record_news"]["type"] == (
            "platformmatrixfinal_record")
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_record")) == 1
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_standing")) == 1
        result = agent.view_platformmatrixfinal("P-02")
        assert result["standing"]["held"] is False
        assert result["record"] is None
        assert result["held_record_news"] is None
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_standing")) == 2
        agent.close()


class TestPlatformMatrixFinalReports:
    def test_prepare_report_holds_and_publishes(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.prepare_platformmatrixfinal_report(
            "matrix-2026-11", "release-1",
            "every cell answered",
            "2026-11-13", 1, 11, 12,
            claims=("local_run_ref", "report_ref"))
        assert result["report"]["state"] == "ready"
        assert result["report"]["certified"] is False
        assert result["report"]["inflated"] is False
        assert result["report_news"]["type"] == (
            "platformmatrixfinal_verdict")
        assert "every cell answered" in result["screen"]
        report = agent.get_platformmatrixfinal_report(
            "matrix-2026-11")
        assert report.entry == "release-1"
        assert [r.book for r in
                agent.platformmatrixfinal_reports()] == [
            "matrix-2026-11"]
        assert len(_pm_records(
            store, session_id, "platformmatrixfinal_verdict")) == 1
        agent.close()

    def test_report_unshared_state_refuses_by_name(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        with pytest.raises(ValidationError, match="ready or shared"):
            agent.prepare_platformmatrixfinal_report(
                "matrix-2026-11", "release-1", "x",
                "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",), state="executed")
        assert agent.platformmatrixfinal_reports() == []
        assert _pm_records(
            store, session_id, "platformmatrixfinal_verdict") == []
        agent.close()

    def test_duplicate_report_refuses(self, agent):
        agent.prepare_platformmatrixfinal_report(
            "matrix-2026-11", "release-1",
            "every cell answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        with pytest.raises(ValueError, match="matrix-2026-11"):
            agent.prepare_platformmatrixfinal_report(
                "matrix-2026-11", "release-2",
                "a second telling", "2026-11-13", 1, 11, 12,
                claims=("local_run_ref",))
        with pytest.raises(ValueError,
                           match="holds no"):
            agent.get_platformmatrixfinal_report("matrix-2026-12")


class TestPlatformMatrixFinalParseArgs:
    def test_parse_args_well(self):
        assert parse_platformmatrixfinal_args("") == (
            "show", None, (), None)
        assert parse_platformmatrixfinal_args(None) == (
            "show", None, (), None)
        assert parse_platformmatrixfinal_args("cells") == (
            "cells", None, (), None)
        assert parse_platformmatrixfinal_args(
            "cell P-01") == (
            "cell", "P-01", (), None)
        assert parse_platformmatrixfinal_args(
            "record P-01") == (
            "record", "P-01", (), None)
        assert parse_platformmatrixfinal_args(
            "standing P-03") == (
            "standing", "P-03", (), None)
        assert parse_platformmatrixfinal_args("report") == (
            "reports", None, (), None)
        assert parse_platformmatrixfinal_args(
            "report matrix-2026-11") == (
            "report", "matrix-2026-11", (), None)
        assert parse_platformmatrixfinal_args("verdict") == (
            "verdict", None, (), None)
        assert parse_platformmatrixfinal_args("index") == (
            "index", None, (), None)

    def test_parse_args_bad_grammar_raises_usage(self):
        for bad in ("dance", "cell", "record",
                    "record P-01 extra",
                    "cells now", "standing",
                    "report a b"):
            with pytest.raises(ValueError) as caught:
                parse_platformmatrixfinal_args(bad)
            assert str(caught.value) == PLATFORMMATRIXFINAL_USAGE


class TestPlatformMatrixFinalTerminalRoad:
    def test_show_cells_cell_record_standing_report_index_verdict(
            self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/platformmatrixfinal")
        assert "P-01" in text
        assert "none recorded this session" in text
        _, _, text = _slash(agent, "/platformmatrixfinal cells")
        assert "macos" in text
        assert "P-12" in text
        _, _, text = _slash(
            agent, "/platformmatrixfinal cell P-01")
        assert "linux" in text
        _, _, text = _slash(
            agent, "/platformmatrixfinal record P-01")
        assert "holds no" in text
        _, _, text = _slash(
            agent, "/platformmatrixfinal standing P-01")
        assert "P-01:" in text
        assert "open" in text
        assert "gap:" in text
        _, _, text = _slash(agent, "/platformmatrixfinal report")
        assert "none held" in text
        _, _, text = _slash(agent, "/platformmatrixfinal verdict")
        assert "Platform matrix final stands open" in text
        agent.register_platformmatrixfinal_record(_pm_record())
        _, _, text = _slash(
            agent, "/platformmatrixfinal record P-01")
        assert "held as answered" in text
        _, _, text = _slash(
            agent, "/platformmatrixfinal standing P-01")
        assert "held as answered" in text
        _, _, text = _slash(agent, "/platformmatrixfinal index")
        assert "held as answered" in text
        agent.prepare_platformmatrixfinal_report(
            "matrix-2026-11", "release-1",
            "every cell answered", "2026-11-13", 1, 11, 12,
            claims=("local_run_ref",))
        _, _, text = _slash(
            agent, "/platformmatrixfinal report matrix-2026-11")
        assert "every cell answered" in text
        assert "never inflated" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/platformmatrixfinal [show|cells|"
                "cell <cell>|"
                "record <cell>|"
                "standing <cell>|"
                "report [<book>]|index|"
                "verdict]") in text
        _, _, text = _slash(agent, "/platformmatrixfinal dance party")
        assert text == PLATFORMMATRIXFINAL_USAGE
        _, _, text = _slash(
            agent, "/platformmatrixfinal cell guess")
        assert "unknown cell" in text


@pytest.fixture()
def pm_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY
    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda record, **kwargs: published.append((record, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _pm_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for record, kwargs in handler.published
                     if record == "agent_chat_chunk")


class TestPlatformMatrixFinalHandler:
    def test_show_is_default(self, pm_handler, agent):
        pm_handler._handle_platformmatrixfinal("")
        assert "P-01" in (
            _pm_published_text(pm_handler))
        assert "linux" in (
            _pm_published_text(pm_handler))

    def test_cell_record_and_verdict(
            self, pm_handler, agent):
        pm_handler._handle_platformmatrixfinal(
            "cell P-01")
        assert "linux" in (
            _pm_published_text(pm_handler))
        agent.register_platformmatrixfinal_record(_pm_record())
        pm_handler._handle_platformmatrixfinal(
            "record P-01")
        assert "held as answered" in (
            _pm_published_text(pm_handler))
        pm_handler._handle_platformmatrixfinal("verdict")
        assert "Platform matrix final stands held" in (
            _pm_published_text(pm_handler))

    def test_bad_grammar_is_published(
            self, pm_handler, agent):
        pm_handler._handle_platformmatrixfinal("dance party")
        assert PLATFORMMATRIXFINAL_USAGE in (
            _pm_published_text(pm_handler))
        pm_handler._handle_platformmatrixfinal("cell guess")
        assert "unknown cell" in (
            _pm_published_text(pm_handler))


class TestChatScreenRoutingPlatformMatrixFinal:
    def test_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import (
            MainChatScreen)

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append(
                (cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/platformmatrixfinal verdict",
                              _FakeLog())
        assert calls == [("/platformmatrixfinal", "verdict")]

    def test_chat_screen_help_and_usage_name_the_matrix(self):
        text = (ROOT / "mythic_agent" / "ui" / "screens"
                / "chat_screen.py").read_text(encoding="utf-8")
        assert ("/platformmatrixfinal[/green] - show the "
                "Platform matrix final (M-259)") in text
        assert ('"/platformmatrixfinal": "Usage: '
                "/platformmatrixfinal | "
                "/platformmatrixfinal cells") in text


class TestPlatformMatrixFinalDerivedRoads:
    def test_index_derives_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        result = agent.platformmatrixfinal_index()
        assert result["index"]["gaps"] == []
        assert result["index"]["held"] == []
        assert result["index"]["total"] == 0
        assert [e for e in store.export(session_id)["events"]
                if e["type"] in _PM_EVENT_TYPES] == []
        agent.close()

    def test_verdict_open_then_held(self, agent):
        verdict = agent.platformmatrixfinal_verdict()
        assert verdict["verdict"]["verdict"] == "open"
        assert verdict["verdict"]["held"] == []
        agent.register_platformmatrixfinal_record(_pm_record())
        agent.register_platformmatrixfinal_record(
            _pm_fresh_for("P-05", run="reproof-2026-11-b"))
        verdict = agent.platformmatrixfinal_verdict()
        assert verdict["verdict"]["verdict"] == "held"
        assert verdict["verdict"]["held"] == [
            "P-01", "P-05"]
        assert "Platform matrix final stands held" in (
            verdict["verdict_text"])

    def test_report_renders_the_session_book(self, agent):
        report = agent.report_platformmatrixfinal()
        assert report["book"]["schema"] == (
            PLATFORM_MATRIX_FINAL_SCHEMA)
        assert report["verdict"]["verdict"] == "open"
        assert report["records_text"] == ""
        agent.register_platformmatrixfinal_record(_pm_record())
        report = agent.report_platformmatrixfinal()
        assert "held as answered" in report["records_text"]
        assert [s["cell"] for s in report["standings"]] == [
            "P-01"]

    def test_records_for_verdict_and_held_keys(self, agent):
        agent.register_platformmatrixfinal_record(_pm_record())
        agent.register_platformmatrixfinal_record(
            _pm_fresh_for("P-05", run="reproof-2026-11-b"))
        agent.register_platformmatrixfinal_record(_pm_record(
            cell="P-02", run="reproof-2026-11-c",
            verdict="NOT PROVEN",
            stages=["named"], claims=["assertion"]))
        assert [r.run for r in
                agent.records_for_verdict("PROVEN")] == [
            "reproof-2026-11-a", "reproof-2026-11-b"]
        assert agent.platformmatrixfinal_held() == ["P-01", "P-05"]
        standing = agent.platformmatrixfinal_standing(
            "P-02")
        assert standing.held is False
