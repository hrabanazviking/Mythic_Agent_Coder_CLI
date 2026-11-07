"""Tests for M-092: blame and history sight (pure layer).

TIER: integration
"""

import pytest

from mythic_agent.core import blame_sight as bs

COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
ZERO = "0" * 40

PORCELAIN = (
    f"{COMMIT_A} 1 1 3\n"
    "author Ada Example\n"
    "author-mail <ada@example.invalid>\n"
    "author-time 1793984433\n"
    "author-tz -0500\n"
    "committer Ada Example\n"
    "committer-mail <ada@example.invalid>\n"
    "committer-time 1793984433\n"
    "committer-tz -0500\n"
    "summary open the file\n"
    "filename demo.py\n"
    "\tfirst = 1\n"
    f"{COMMIT_A} 2 2\n"
    "\tsecond = 2\n"
    f"{COMMIT_A} 3 3\n"
    "\tthird = 3\n"
    f"{COMMIT_B} 2 4 1\n"
    "author Ben Example\n"
    "author-mail <ben@example.invalid>\n"
    "author-time 1794070833\n"
    "author-tz -0500\n"
    "summary the fourth line arrives later\n"
    "filename demo.py\n"
    "\tfourth = 4\n"
    f"{ZERO} 5 5 1\n"
    "author Not Committed Yet\n"
    "author-mail <not.committed.yet>\n"
    "author-time 1794157233\n"
    "author-tz -0500\n"
    "summary work in progress\n"
    "filename demo.py\n"
    "\tfifth = 5\n"
)


# --- porcelain parsing: blamed, never invented -----------------

def test_parse_counts_every_line():
    lines = bs.parse_blame_porcelain(PORCELAIN)
    assert len(lines) == 5
    assert [x.line_no for x in lines] == [1, 2, 3, 4, 5]


def test_first_entry_carries_its_commit_record():
    entry = bs.parse_blame_porcelain(PORCELAIN)[0]
    assert entry.commit == COMMIT_A
    assert entry.author == "Ada Example"
    assert entry.author_mail == "<ada@example.invalid>"
    assert entry.author_time == 1793984433
    assert entry.summary == "open the file"
    assert entry.filename == "demo.py"
    assert entry.text == "first = 1"


def test_group_lines_inherit_the_commit_record():
    lines = bs.parse_blame_porcelain(PORCELAIN)
    for entry in lines[1:3]:
        assert entry.commit == COMMIT_A
        assert entry.author == "Ada Example"
        assert entry.summary == "open the file"


def test_orig_and_final_line_numbers_are_kept_apart():
    entry = bs.parse_blame_porcelain(PORCELAIN)[3]
    assert entry.orig_no == 2 and entry.line_no == 4


def test_second_commit_has_its_own_record():
    entry = bs.parse_blame_porcelain(PORCELAIN)[3]
    assert entry.author == "Ben Example"
    assert entry.summary == "the fourth line arrives later"


def test_uncommitted_line_is_flagged_not_dressed_up():
    entry = bs.parse_blame_porcelain(PORCELAIN)[4]
    assert entry.uncommitted is True
    assert entry.commit == ZERO
    assert bs.parse_blame_porcelain(PORCELAIN)[0].uncommitted is False


def test_empty_porcelain_parses_to_no_lines():
    assert bs.parse_blame_porcelain("") == ()


def test_junk_line_raises_instead_of_being_blamed():
    with pytest.raises(ValueError, match="unreadable line"):
        bs.parse_blame_porcelain("this is not porcelain\n")


def test_content_without_header_raises():
    with pytest.raises(ValueError, match="no header"):
        bs.parse_blame_porcelain("\torphan = 1\n")


def test_header_without_content_raises():
    with pytest.raises(ValueError, match="no content line"):
        bs.parse_blame_porcelain(
            f"{COMMIT_A} 1 1 1\n"
            "author Ada Example\n"
            "filename demo.py\n")


def test_commit_without_author_record_raises():
    with pytest.raises(ValueError, match="no author record"):
        bs.parse_blame_porcelain(
            f"{COMMIT_A} 1 1 1\n"
            "filename demo.py\n"
            "\tfirst = 1\n")


def test_entry_record_closes():
    record = bs.parse_blame_porcelain(PORCELAIN)[0].record()
    assert record["short_commit"] == COMMIT_A[:7]
    assert record["line_no"] == 1 and record["orig_no"] == 1
    assert record["uncommitted"] is False


# --- one line, runs, and the counted header --------------------

def test_blame_line_finds_the_asked_line():
    lines = bs.parse_blame_porcelain(PORCELAIN)
    assert bs.blame_line(lines, 4).text == "fourth = 4"


def test_blame_line_outside_the_file_raises():
    lines = bs.parse_blame_porcelain(PORCELAIN)
    with pytest.raises(ValueError, match="outside the blamed file"):
        bs.blame_line(lines, 6)
    with pytest.raises(ValueError, match="start at 1"):
        bs.blame_line(lines, 0)


def test_runs_group_consecutive_lines_by_commit():
    runs = bs.blame_runs(bs.parse_blame_porcelain(PORCELAIN))
    assert [(r.commit, r.start_line, r.end_line, r.count)
            for r in runs] == [
        (COMMIT_A, 1, 3, 3), (COMMIT_B, 4, 4, 1),
        (ZERO, 5, 5, 1)]


def test_runs_split_when_a_commit_returns():
    text = (
        f"{COMMIT_A} 1 1 1\n"
        "author Ada Example\n"
        "author-time 1793984433\n"
        "summary one\n"
        "filename demo.py\n"
        "\tone\n"
        f"{COMMIT_B} 1 2 1\n"
        "author Ben Example\n"
        "author-time 1794070833\n"
        "summary two\n"
        "filename demo.py\n"
        "\ttwo\n"
        f"{COMMIT_A} 1 3 1\n"
        "\tthree\n")
    runs = bs.blame_runs(bs.parse_blame_porcelain(text))
    assert [r.commit for r in runs] == [COMMIT_A, COMMIT_B, COMMIT_A]


def test_format_blame_header_counts_from_the_blame():
    text = bs.format_blame(bs.parse_blame_porcelain(PORCELAIN))
    assert "Blame for demo.py: 5 lines, 3 commits, 3 authors" in text
    assert "(not committed yet)" in text


# --- the journal half: the session that wrote it ---------------

def _journal(*entries):
    return list(entries)


def test_journal_span_match_names_the_session():
    sight = bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 2, _journal(
            {"type": "edit_applied", "path": "demo.py",
             "start_line": 1, "end_line": 3,
             "session_id": "sess-1"}))
    assert sight.journal_session == "sess-1"
    assert "sess-1" in sight.journal_note


def test_journal_single_line_and_lines_list_match():
    lines = bs.parse_blame_porcelain(PORCELAIN)
    one = bs.explain_line(lines, 3, _journal(
        {"path": "demo.py", "line": 3, "session_id": "sess-line"}))
    assert one.journal_session == "sess-line"
    many = bs.explain_line(lines, 3, _journal(
        {"path": "demo.py", "lines": [2, 3, 4],
         "session_id": "sess-list"}))
    assert many.journal_session == "sess-list"


def test_newest_line_record_wins():
    sight = bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 2, _journal(
            {"path": "demo.py", "line": 2,
             "session_id": "sess-old"},
            {"path": "demo.py", "line": 2,
             "session_id": "sess-new"}))
    assert sight.journal_session == "sess-new"
    assert sight.journal_line_records == 2


def test_file_level_record_does_not_name_a_session():
    sight = bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 2, _journal(
            {"type": "session_opened", "path": "demo.py",
             "session_id": "sess-file"}))
    assert sight.journal_session is None
    assert sight.journal_file_records == 1
    assert "none covers this line" in sight.journal_note


def test_other_files_records_are_not_this_lines_history():
    sight = bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 2, _journal(
            {"path": "other.py", "line": 2,
             "session_id": "sess-other"}))
    assert sight.journal_session is None
    assert "no journal record covers this line" in sight.journal_note


def test_no_journal_says_blame_alone_speaks():
    sight = bs.explain_line(bs.parse_blame_porcelain(PORCELAIN), 1)
    assert sight.journal_session is None
    assert "blame alone speaks" in sight.journal_note


def test_uncommitted_line_note_says_no_commit():
    sight = bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 5, _journal(
            {"path": "demo.py", "line": 5,
             "session_id": "sess-wip"}))
    assert sight.uncommitted is True
    assert sight.journal_session == "sess-wip"
    assert "not committed yet" in sight.journal_note


def test_dot_slash_paths_match_the_blamed_name():
    match = bs.match_journal(
        [{"path": "./demo.py", "line": 2,
          "session_id": "sess-dot"}], "demo.py", 2)
    assert match.session == "sess-dot"


def test_malformed_journal_records_raise():
    with pytest.raises(ValueError, match="must be records"):
        bs.match_journal(["not a record"], "demo.py", 1)
    with pytest.raises(ValueError, match="positive"):
        bs.journal_span({"line": 0})


def test_explain_record_carries_both_halves():
    record = bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 4, _journal(
            {"path": "demo.py", "line": 4,
             "session_id": "sess-4"})).record()
    assert record["commit"] == COMMIT_B
    assert record["author"] == "Ben Example"
    assert record["journal_session"] == "sess-4"
    assert record["type"] == "blame_sight"


def test_format_history_sight_names_commit_author_session():
    text = bs.format_history_sight(bs.explain_line(
        bs.parse_blame_porcelain(PORCELAIN), 4, _journal(
            {"path": "demo.py", "line": 4,
             "session_id": "sess-4"})))
    assert "Line 4 of demo.py: fourth = 4" in text
    assert COMMIT_B[:7] in text and "Ben Example" in text
    assert "sess-4" in text


# --- gate and grammar -------------------------------------------

def test_gate_absent_means_on_and_malformed_raises():
    assert bs.enabled_from_config({}) is True
    assert bs.enabled_from_config({"blame_sight": False}) is False
    with pytest.raises(ValueError, match="true or false"):
        bs.enabled_from_config({"blame_sight": "yes"})


def test_set_enabled_records_the_change():
    enabled, change = bs.set_enabled({}, False)
    assert enabled is False
    assert change.event() == {
        "type": "blame_sight_setting_changed",
        "from": True, "to": False}
    with pytest.raises(ValueError, match="already on"):
        bs.set_enabled({}, True)
    with pytest.raises(ValueError, match="turned on or off"):
        bs.set_enabled({}, "off")


def test_parse_args_grammar():
    assert bs.parse_blame_args("") == {"action": "show"}
    assert bs.parse_blame_args("on") == {"action": "on"}
    assert bs.parse_blame_args("off") == {"action": "off"}
    assert bs.parse_blame_args("demo.py") == {
        "action": "blame", "path": "demo.py", "line": None}
    assert bs.parse_blame_args("demo.py 4") == {
        "action": "blame", "path": "demo.py", "line": 4}
    assert bs.parse_blame_args("demo.py:4") == {
        "action": "blame", "path": "demo.py", "line": 4}


def test_parse_args_bad_line_and_extra_words_raise():
    with pytest.raises(ValueError, match="usage"):
        bs.parse_blame_args("demo.py fourth")
    with pytest.raises(ValueError, match="start at 1"):
        bs.parse_blame_args("demo.py 0")
    with pytest.raises(ValueError, match="usage"):
        bs.parse_blame_args("demo.py 4 extra words here")


def test_format_blame_sight_show_surface_exercises_the_road():
    text = bs.format_blame_sight({})
    assert "Blame and history sight (M-092)" in text
    assert "Setting: on (blame_sight)." in text
    assert "Blame for demo.py: 3 lines, 2 commits, 2 authors" in text
    assert "demo-session" in text
    assert bs.format_setting_change({"to": False}) == (
        "Blame sight is now off.")


# --- agent layer: gate, sight road, surfaces ----------------

import subprocess

from mythic_agent.core.sessions import SessionStore


def _git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _repo(tmp_path):
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Slice Test")
    (tmp_path / "demo.py").write_text(
        "first = 1\nsecond = 2\nthird = 3\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "open the demo file")
    return tmp_path


def _store_for(tmp_path):
    return SessionStore(tmp_path, tmp_path / "state")


class TestBlameAgentGate:
    def test_status(self, agent):
        status = agent.blame_sight_status()
        assert status["enabled"] is True
        assert status["explanation"] == bs.PLAIN_EXPLANATION

    def test_set_without_session(self, agent):
        record = agent.set_blame_sight(False)
        assert record["journaled"] is False
        assert agent.config["blame_sight"] is False
        with pytest.raises(ValueError, match="already"):
            agent.set_blame_sight(False)

    def test_set_journals_on_the_session(self, agent, tmp_path):
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent.set_blame_sight(False)
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "blame_sight_setting_changed" in types
        agent.close()

    def test_save_failure_restores_and_journals_the_revert(
            self, agent, tmp_path, monkeypatch):
        from mythic_agent.agents import llm

        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        monkeypatch.setattr(llm.config_manager, "save_config",
                            lambda config: False)
        with pytest.raises(RuntimeError, match="could not be saved"):
            agent.set_blame_sight(False)
        assert agent.config.get("blame_sight") is not False
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert types[-2:] == ["blame_sight_setting_changed",
                              "blame_sight_setting_reverted"]
        agent.close()


class TestBlameSightRoad:
    def test_line_sight_names_the_commit(self, agent, tmp_path):
        _repo(tmp_path)
        record = agent.show_blame_sight("demo.py", 2)
        assert record["type"] == "blame_sight"
        assert record["author"] == "Slice Test"
        assert record["summary"] == "open the demo file"
        assert record["uncommitted"] is False
        assert record["journal_session"] is None
        assert "blame alone speaks" in record["journal_note"]
        assert "Line 2 of demo.py" in record["rendered"]
        assert record["journaled"] is False

    def test_whole_file_blame(self, agent, tmp_path):
        _repo(tmp_path)
        record = agent.show_blame_sight("demo.py")
        assert record["lines"] == 3
        assert "Blame for demo.py: 3 lines" in record["rendered"]

    def test_uncommitted_line_is_flagged(self, agent, tmp_path):
        _repo(tmp_path)
        with open(tmp_path / "demo.py", "a", encoding="utf-8") as fh:
            fh.write("fourth = 4\n")
        record = agent.show_blame_sight("demo.py", 4)
        assert record["uncommitted"] is True
        assert "not committed yet" in record["rendered"]

    def test_journal_session_is_named(self, agent, tmp_path):
        _repo(tmp_path)
        store = _store_for(tmp_path)
        session_id = agent.attach_session(store)
        agent._checkpoint({"type": "edit_applied",
                           "path": "demo.py", "line": 2})
        record = agent.show_blame_sight("demo.py", 2)
        assert record["journal_session"] == session_id
        assert record["journaled"] is True
        types = [e["type"] for e in store.export(session_id)["events"]]
        assert "blame_sight" in types
        agent.close()

    def test_gate_off_refuses_and_blames_nothing(self, agent, tmp_path):
        _repo(tmp_path)
        agent.set_blame_sight(False)
        with pytest.raises(ValueError, match="blame sight is off"):
            agent.show_blame_sight("demo.py", 1)

    def test_missing_file_refuses_with_gits_words(self, agent, tmp_path):
        _repo(tmp_path)
        with pytest.raises(ValueError, match="git blame could not read"):
            agent.show_blame_sight("nope.py", 1)


class TestBlameTerminalSurface:
    def test_show_and_set(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/blame")
        assert "Blame and history sight (M-092)" in text
        assert "Setting: on (blame_sight)" in text
        _, _, text = _slash(agent, "/blame off")
        assert "Blame sight is now off." in text
        assert agent.config["blame_sight"] is False
        _, _, text = _slash(agent, "/blame on")
        assert "Blame sight is now on." in text

    def test_blame_via_the_terminal(self, agent, tmp_path):
        from mythic_agent.terminal import _slash

        _repo(tmp_path)
        _, _, text = _slash(agent, "/blame demo.py 2")
        assert "Line 2 of demo.py" in text
        _, _, text = _slash(agent, "/blame demo.py")
        assert "Blame for demo.py: 3 lines" in text

    def test_usage_error_is_the_message(self, agent):
        from mythic_agent.terminal import _slash

        _, _, text = _slash(agent, "/blame a b c")
        assert "Usage: /blame" in text


@pytest.fixture()
def blame_handler(agent, monkeypatch):
    from mythic_agent.agents import command_handler as handler_module
    from mythic_agent.agents.command_handler import CommandHandler
    from mythic_agent.agents.llm import AGENT_REGISTRY

    published = []
    monkeypatch.setattr(
        handler_module, "publish_sync",
        lambda event, **kwargs: published.append((event, kwargs)))
    AGENT_REGISTRY["Primary"] = agent
    instance = CommandHandler.__new__(CommandHandler)
    instance.published = published
    yield instance
    AGENT_REGISTRY.pop("Primary", None)


def _blame_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestBlameCommand:
    def test_show_is_default(self, blame_handler, agent):
        blame_handler._handle_blame("")
        assert "Blame and history sight (M-092)" in _blame_published_text(
            blame_handler)

    def test_set_via_the_handler(self, blame_handler, agent):
        blame_handler._handle_blame("off")
        assert "Blame sight is now off." in _blame_published_text(
            blame_handler)
        assert agent.config["blame_sight"] is False

    def test_blame_via_the_handler(self, blame_handler, agent, tmp_path):
        _repo(tmp_path)
        blame_handler._handle_blame("demo.py 2")
        assert "Line 2 of demo.py" in _blame_published_text(blame_handler)

    def test_usage_error_is_published(self, blame_handler, agent):
        blame_handler._handle_blame("a b c")
        assert "Usage: /blame" in _blame_published_text(blame_handler)
