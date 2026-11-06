"""M-083 — Issue-to-slice.

TIER: integration

Covers the M-083 surface: the pure layer
(mythic_agent.core.issue_slice) drafting acceptance checks
only from an issue's own words, the source seam (github
fetches via the gh road, samverk named for Part X M-242 and
refusing honestly), the Agent gate/plan/journal road, the
terminal and TUI surfaces sharing one parser/formatters,
and the config contract (issue_to_slice ships True; its
M-009 catalogue entry S-64 is a coordinator delta).
"""
from __future__ import annotations
import pytest
from mythic_agent.core.issue_slice import (
    CHECK_KINDS, ISSUE_SLICE_SLICE, PLAIN_EXPLANATION,
    PLANNED_STATUS, SAMVERK_ROAD, SETTING_KEY,
    AcceptanceCheck, IssueRecord, IssueSourceUnavailable,
    available_sources, draft_acceptance_checks,
    enabled_from_config, fetch_issue, format_issue_slice,
    format_plan, format_plan_record, format_setting_change,
    issue_from_github_record, issue_from_record,
    parse_issueslice_args, plan_slice, set_enabled,
    validate_checks_trace,
)
from mythic_agent.core.sessions import SessionStore

BODY = ("Opening an empty file crashes the editor.\n\n"
        "- [ ] An empty file opens without crashing\n"
        "- [x] A file with one line still opens\n\n"
        "## Acceptance criteria\n\n"
        "- The crash report names the empty-file case\n"
        "- No data is lost\n\n"
        "## Notes\n\n- An unrelated bullet\n")

def make_issue(**kw):
    base = dict(source="github", number=7,
                title="Fix the crash on an empty file",
                body=BODY, state="open", labels=("bug",),
                url="https://github.com/example/repo/issues/7")
    base.update(kw)
    return IssueRecord(**base)

def store_for(tmp_path, workspace=None):
    return SessionStore(workspace or tmp_path, tmp_path / "state")

class TestBuild:
    def test_constants(self):
        assert ISSUE_SLICE_SLICE == "M-083"
        assert SETTING_KEY == "issue_to_slice"
        assert PLANNED_STATUS == "planned"
        assert SAMVERK_ROAD == "M-242"
        assert CHECK_KINDS == ("checklist", "acceptance", "title")
        assert "own words" in PLAIN_EXPLANATION
    def test_sources_registry(self):
        infos = available_sources()
        assert [i.name for i in infos] == ["github", "samverk"]
        assert infos[0].available is True and infos[0].road == "M-083"
        assert infos[1].available is False and infos[1].road == "M-242"
    def test_source_ref(self):
        assert make_issue().source_ref() == "github#7"

class TestIssueFromRecord:
    def test_plain_record(self):
        issue = issue_from_record({"number": 3, "title": " T ", "body": "b", "labels": ["a", {"name": "b"}]})
        assert issue.title == "T" and issue.labels == ("a", "b")
        assert issue.state == "open" and issue.url == ""
    def test_github_record(self):
        issue = issue_from_github_record({"number": 1, "title": "X", "labels": [{"name": "bug"}]})
        assert issue.source == "github" and issue.labels == ("bug",)
    def test_bad_records_refuse(self):
        with pytest.raises(ValueError):
            issue_from_record("nope")
        with pytest.raises(ValueError, match="number"):
            issue_from_record({"number": 0, "title": "X"})
        with pytest.raises(ValueError, match="title"):
            issue_from_record({"number": 1, "title": "  "})
        with pytest.raises(ValueError, match="unknown issue source"):
            issue_from_record({"number": 1, "title": "X"}, source="nope")

class TestDrafting:
    def test_checklist_and_acceptance_drafted_in_order(self):
        checks = draft_acceptance_checks(make_issue())
        assert [c.kind for c in checks] == ["checklist", "checklist", "acceptance", "acceptance"]
        assert checks[0].text == "An empty file opens without crashing"
        assert checks[0].source_excerpt == checks[0].text
        assert "unrelated" not in " ".join(c.text for c in checks)
    def test_title_fallback(self):
        checks = draft_acceptance_checks(make_issue(body="Just prose.\n"))
        assert len(checks) == 1 and checks[0].kind == "title"
        assert checks[0].source_excerpt == "Fix the crash on an empty file"
    def test_dedupe(self):
        body = "- [ ] Same thing\n- [ ] Same thing\n"
        checks = draft_acceptance_checks(make_issue(body=body))
        assert len(checks) == 1
    def test_trace_validation(self):
        issue = make_issue()
        assert validate_checks_trace(issue, draft_acceptance_checks(issue)) == []
        bad = AcceptanceCheck(text="Invented", kind="checklist", source_excerpt="not in the issue at all")
        problems = validate_checks_trace(issue, (bad,))
        assert problems and "own words" in problems[0]
        badkind = AcceptanceCheck(text="X", kind="magic", source_excerpt="Fix the crash on an empty file")
        assert validate_checks_trace(issue, (badkind,))

class TestPlan:
    def test_plan_shape(self):
        plan = plan_slice(make_issue())
        assert plan.status == "planned" and plan.title.startswith("Fix the crash")
        assert plan.summary == "Opening an empty file crashes the editor."
        rec = plan.to_record()
        assert rec["status"] == "planned" and rec["source_ref"] == "github#7"
        assert rec["labels"] == ["bug"] and len(rec["acceptance_checks"]) == 4
        assert plan.event()["type"] == "issue_slice_planned"
        assert plan.record(None, False)["journaled"] is False
    def test_summary_falls_back_to_title(self):
        plan = plan_slice(make_issue(body="## Only a heading\n"))
        assert plan.summary == plan.title
    def test_plan_refuses_non_issue(self):
        with pytest.raises(ValueError):
            plan_slice({"title": "x"})
    def test_formatters(self):
        plan = plan_slice(make_issue())
        text = format_plan(plan)
        assert "Planned slice from github#7" in text and "Acceptance checks (4)" in text
        assert format_plan_record(plan.to_record()) == text
        shown = format_issue_slice({})
        assert "Issue-to-slice (M-083)" in shown and "samverk" in shown
        assert "Setting: on (issue_to_slice)" in shown
        assert "Setting: off" in format_issue_slice({"issue_to_slice": False})

class TestSeam:
    def test_fetch_with_fake_fetcher(self):
        issue = fetch_issue("github", 9, fetcher=lambda n: {"number": n, "title": "Fake", "body": "- [ ] Do it\n"})
        assert issue.number == 9 and issue.title == "Fake"
    def test_samverk_refuses_honestly(self):
        with pytest.raises(IssueSourceUnavailable, match="M-242"):
            fetch_issue("samverk", 1)
    def test_unknown_source_and_bad_number(self):
        with pytest.raises(ValueError, match="unknown issue source"):
            fetch_issue("nope", 1)
        with pytest.raises(ValueError, match="1 or more"):
            fetch_issue("github", 0, fetcher=lambda n: {})
    def test_github_view_issue_stubbed(self, monkeypatch):
        from mythic_agent.integrations import github
        monkeypatch.setattr(github, "_run_gh", lambda *a: '{"number": 5, "title": "T5", "body": "b", "state": "open", "labels": [{"name": "x"}], "url": "u"}')
        rec = github.view_issue(5)
        assert rec["title"] == "T5"
        with pytest.raises(ValueError):
            github.view_issue(0)

class TestGateAndParse:
    def test_gate(self):
        assert enabled_from_config({}) is True
        assert enabled_from_config({"issue_to_slice": False}) is False
        with pytest.raises(ValueError, match="true or false"):
            enabled_from_config({"issue_to_slice": "yes"})
        value, change = set_enabled({}, False)
        assert value is False and change.before is True
        assert change.event()["type"] == "issue_slice_setting_changed"
        with pytest.raises(ValueError, match="already on"):
            set_enabled({}, True)
        with pytest.raises(ValueError):
            set_enabled({}, "off")
    def test_parse(self):
        assert parse_issueslice_args("") == {"action": "show"}
        assert parse_issueslice_args("on") == {"action": "setting", "enabled": True}
        assert parse_issueslice_args("off") == {"action": "setting", "enabled": False}
        assert parse_issueslice_args("github 42") == {"action": "plan", "source": "github", "number": 42}
        assert parse_issueslice_args("github #7")["number"] == 7
        with pytest.raises(ValueError, match="Usage"):
            parse_issueslice_args("sideways")
        with pytest.raises(ValueError):
            parse_issueslice_args("nope 1")
    def test_format_setting_change(self):
        assert format_setting_change({"from": True, "to": False}) == "Issue-to-slice: on -> off."

class TestAgent:
    def test_status(self, agent):
        status = agent.issue_slice_status()
        assert status["enabled"] is True and status["explanation"] == PLAIN_EXPLANATION
    def test_set_without_session(self, agent):
        record = agent.set_issue_slice(False)
        assert record["journaled"] is False and agent.config["issue_to_slice"] is False
    def test_set_journals(self, agent, tmp_path):
        store = store_for(tmp_path); sid = agent.attach_session(store)
        agent.set_issue_slice(False)
        types = [e["type"] for e in store.export(sid)["events"]]
        assert "issue_slice_setting_changed" in types; agent.close()
    def test_save_failure_reverts(self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm
        store = store_for(tmp_path); sid = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config", lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_issue_slice(False)
        assert agent.config.get("issue_to_slice") is not False
        types = [e["type"] for e in store.export(sid)["events"]]
        assert types[-2:] == ["issue_slice_setting_changed", "issue_slice_setting_reverted"]; agent.close()
    def test_plan_with_fake_fetcher_journals(self, agent, tmp_path):
        store = store_for(tmp_path); sid = agent.attach_session(store)
        rec = agent.plan_issue_slice("github", 7, fetcher=lambda n: {"number": 7, "title": "Fix the crash on an empty file", "body": BODY, "labels": [{"name": "bug"}]})
        assert rec["status"] == "planned" and len(rec["acceptance_checks"]) == 4
        types = [e["type"] for e in store.export(sid)["events"]]
        assert "issue_slice_planned" in types; agent.close()
    def test_draft_from_record_and_gate_off(self, agent):
        rec = agent.draft_slice_from_issue({"number": 2, "title": "Plain", "body": "Do the thing.\n"})
        assert rec["title"] == "Plain" and rec["journaled"] is False
        agent.set_issue_slice(False)
        with pytest.raises(ValueError, match="issue-to-slice is off"):
            agent.draft_slice_from_issue({"number": 2, "title": "Plain"})
        with pytest.raises(ValueError, match="issue-to-slice is off"):
            agent.plan_issue_slice("github", 1, fetcher=lambda n: {"number": 1, "title": "X"})

class TestSurfaces:
    def test_terminal(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/issueslice")
        assert "Issue-to-slice (M-083)" in text
        _, _, text = _slash(agent, "/issueslice off")
        assert "on -> off" in text and agent.config["issue_to_slice"] is False
        _, _, text = _slash(agent, "/issueslice sideways")
        assert "Usage" in text
    def test_handler_show_and_set(self, agent, monkeypatch):
        from mythic_agent.agents import command_handler as hm
        from mythic_agent.agents.command_handler import CommandHandler
        from mythic_agent.agents.llm import AGENT_REGISTRY
        published = []
        monkeypatch.setattr(hm, "publish_sync", lambda event, **kw: published.append((event, kw)))
        AGENT_REGISTRY["Primary"] = agent
        try:
            h = CommandHandler.__new__(CommandHandler); h.published = published
            h._handle_issueslice("")
            text = "\n".join(kw.get("text", "") for ev, kw in published if ev == "agent_chat_chunk")
            assert "Issue-to-slice (M-083)" in text
            h._handle_issueslice("off")
            assert agent.config["issue_to_slice"] is False
        finally:
            AGENT_REGISTRY.pop("Primary", None)
    def test_chat_routing(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen
        class FakeLog:
            def write(self, *a, **k): pass
        calls = []
        monkeypatch.setattr(chat_screen.SecureAPI, "publish_system_command", staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command("/issueslice off", FakeLog())
        assert calls == [("/issueslice", "off")]

class TestConfigContract:
    def test_defaults_ship_on(self):
        import yaml
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        defaults = yaml.safe_load((root / "mythic_agent/data/config_defaults.yaml").read_text(encoding="utf-8"))
        assert defaults["issue_to_slice"] is True
