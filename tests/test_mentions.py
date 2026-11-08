"""M-148 The @-mention canon - pure-layer tests.

TIER: integration

The pure layer is the @-mention grammar as data:
a mention canon book of mention records (one pull
named in text - its kind in the closed set the
roadmap itself names, its target judged against
its kind, the exact text that named it, its
source, and the plain-words reason it is pulled),
the shipped example canon held in a data file, a
loader that reads a canon from any file, a parser
for mention text (the typed forms and the shipped
bare form of Slice 056), a resolution plan derived
from a mention (the shipped road that would pull
its kind, named - never run), an index derived
from the whole book, records shaped as session
news, and a registry. Nothing here reads a file,
fetches a page, compiles a context or persists
anything: a stored plan disagreeing with the plan
derived from its own mention is refused, and a
stored index disagreeing with the index derived
from its book is refused. Parsing and planning
pull nothing in by themselves.
"""

from pathlib import Path

import pytest
import yaml

from mythic_agent.core.validation import ValidationError
from mythic_agent.core.mentions import (
    PLAIN_EXPLANATION,
    MENTIONS_RESOURCE,
    MENTIONS_SCHEMA,
    MENTIONS_SLICE,
    MENTION_KINDS,
    MENTION_ROADS,
    USAGE,
    Mention,
    MentionCanon,
    MentionIndex,
    MentionKindCount,
    MentionPlan,
    MentionRegistry,
    book_record,
    build_canon,
    build_index,
    build_mention,
    build_plan,
    derive_index,
    derive_plan,
    format_mention,
    format_mention_text,
    format_mentions,
    format_mentions_screen,
    format_index,
    format_plan,
    index_plain_words,
    index_record,
    load_mentions,
    load_mentions_file,
    mention_record,
    normalize_kind,
    parse_mention,
    parse_mentions,
    parse_mentions_args,
    plan_plain_words,
    plan_record,
    plain_words,
    validate_book,
    validate_index,
    validate_mention,
    validate_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def _mention(**kwargs):
    kwargs.setdefault("mention_id", "mention-file-context-budget")
    kwargs.setdefault("kind", "file")
    kwargs.setdefault("target", "mythic_agent/core/context_budget.py")
    kwargs.setdefault("source", "M-148 slice note")
    kwargs.setdefault(
        "reason", "The M-147 pure layer is this slice's template.")
    return Mention(**kwargs)


def _mentions():
    return [
        _mention(),
        Mention(
            mention_id="mention-symbol-token-estimator",
            kind="symbol", target="TokenEstimator",
            source="M-148 slice note",
            reason="The shipped token counter, named here."),
        Mention(
            mention_id="mention-file-mentions",
            kind="file", target="mythic_agent/core/mentions.py",
            source="M-148 slice note",
            reason="This slice's own pure layer."),
        Mention(
            mention_id="mention-issue-148",
            kind="issue", target="#148",
            source="M-148 slice note",
            reason="This slice's own roadmap issue word."),
    ]


def _plan_mapping(plan):
    return {
        "mention_id": plan.mention_id,
        "kind": plan.kind,
        "target": plan.target,
        "road": plan.road,
        "action": plan.action,
        "pulls": plan.pulls}


def _index_mapping(index):
    return {
        "index_id": index.index_id,
        "rows": [_plan_mapping(r) for r in index.rows],
        "total_mentions": index.total_mentions,
        "kind_counts": [c.to_record() for c in index.kind_counts],
        "account": list(index.account)}


def test_constants_and_usage():
    assert MENTIONS_SLICE == "M-148"
    assert MENTIONS_SCHEMA == "mythic.mentions/1"
    assert MENTIONS_RESOURCE == "mentions.yaml"
    assert MENTION_KINDS == (
        "file", "folder", "symbol", "url",
        "image", "session", "issue")
    assert set(MENTION_ROADS) == set(MENTION_KINDS)
    assert "resolve_mentions" in MENTION_ROADS["file"]
    assert "build_repo_map" in MENTION_ROADS["folder"]
    assert "select_by_symbols" in MENTION_ROADS["symbol"]
    assert "web_fetch" in MENTION_ROADS["url"]
    assert "vision_routing" in MENTION_ROADS["image"]
    assert "SessionStore" in MENTION_ROADS["session"]
    assert "issue_slice" in MENTION_ROADS["issue"]
    assert "one grammar" in PLAIN_EXPLANATION
    assert "data" in PLAIN_EXPLANATION and "only" in PLAIN_EXPLANATION
    assert USAGE.startswith("Usage: /mentions")
    assert "/mentions mention <mention-id>" in USAGE
    assert "/mentions kind <kind>" in USAGE
    assert "/mentions plan <mention-id>" in USAGE
    assert "/mentions parse <text>" in USAGE
    assert "/mentions index" in USAGE


def test_shipped_example_shape():
    book = load_mentions()
    assert isinstance(book, MentionCanon)
    assert book.title == "Mention canon at the M-147 slice boundary"
    assert book.mention_ids() == (
        "mention-file-context-budget", "mention-folder-context",
        "mention-symbol-token-estimator", "mention-url-ast-docs",
        "mention-image-kiosk-snapshot", "mention-session-m147",
        "mention-issue-148")
    assert book.kinds() == MENTION_KINDS
    first = book.mentions[0]
    assert first.kind == "file"
    assert first.target == "mythic_agent/core/context_budget.py"
    assert book.mention_for("mention-url-ast-docs").kind == "url"
    assert [e.mention_id for e in book.mentions_for_kind("file")] == [
        "mention-file-context-budget"]
    with pytest.raises(KeyError):
        book.mention_for("mention-nope")


def test_shipped_plans_and_index():
    book = load_mentions()
    assert [p.mention_id for p in book.plans] == list(book.mention_ids())
    for plan, entry in zip(book.plans, book.mentions):
        assert plan == derive_plan(entry)
        assert plan.road == MENTION_ROADS[entry.kind]
    assert [i.index_id for i in book.indexes] == ["index-m147-boundary"]
    index = book.index_for("index-m147-boundary")
    assert isinstance(index, MentionIndex)
    assert index.total_mentions == 7
    assert [(c.kind, c.mentions) for c in index.kind_counts] == [
        (kind, 1) for kind in MENTION_KINDS]
    derived = derive_index(book)
    assert derived.rows == index.rows
    assert derived.account == index.account
    assert book.plan_for("mention-symbol-token-estimator").target == (
        "TokenEstimator")
    assert index.row_for("mention-issue-148").kind == "issue"
    with pytest.raises(KeyError):
        book.index_for("index-nope")


def test_mention_validation_and_aliases():
    entry = validate_mention({
        "id": "mention-x", "kind": "FILE",
        "target": "a/b.py", "origin": "a note",
        "why": "Named in the note.", "text": "@a/b.py"})
    assert entry.mention_id == "mention-x"
    assert entry.kind == "file"
    assert entry.source == "a note"
    assert entry.reason == "Named in the note."
    assert entry.raw == "@a/b.py"
    assert build_mention(entry) is entry
    with pytest.raises(ValueError):
        validate_mention({
            "kind": "file", "target": "a/b.py",
            "source": "one", "origin": "two",
            "reason": "Named."})
    with pytest.raises(ValueError):
        validate_mention({
            "kind": "file", "target": "a/b.py", "source": "s",
            "reason": "Named.", "plan": "stored loose"})
    with pytest.raises(ValueError):
        validate_mention({"kind": "file", "source": "s",
                          "reason": "Named."})
    with pytest.raises(ValueError):
        validate_mention("not a mapping")


def test_target_judged_per_kind():
    def bad(kind, target):
        with pytest.raises(ValueError):
            Mention(kind=kind, target=target, source="s",
                    reason="Named for the test.")
    bad("url", "docs.python.org/3/library/ast.html")
    bad("url", "ftp://example.com/x")
    bad("symbol", "some/path.py")
    bad("symbol", "9lives")
    bad("file", "a file with spaces.py")
    bad("session", "a session with spaces")
    bad("issue", "issue #12 please")
    ok = Mention(kind="symbol", target="mod.TokenEstimator",
                 source="s", reason="Named for the test.")
    assert ok.target == "mod.TokenEstimator"
    ok = Mention(kind="issue", target="148", source="s",
                 reason="Named for the test.")
    assert ok.target == "148"


def test_normalize_kind():
    assert normalize_kind("FILE") == "file"
    assert normalize_kind(" Issue ") == "issue"
    with pytest.raises(ValueError) as excinfo:
        normalize_kind("bogus")
    assert "file/folder/symbol/url/image/session/issue" in str(
        excinfo.value)


def test_parse_typed_forms_all_kinds():
    text = (
        "Read @file:src/main.py, map @folder:src/pkg, find "
        "@symbol:TokenEstimator, fetch "
        "@url:https://example.com/docs, view "
        "@image:assets/shot.png, recall @session:sess-1 "
        "and @issue:#42 please.")
    found = parse_mentions(text)
    assert [(m.kind, m.target) for m in found] == [
        ("file", "src/main.py"),
        ("folder", "src/pkg"),
        ("symbol", "TokenEstimator"),
        ("url", "https://example.com/docs"),
        ("image", "assets/shot.png"),
        ("session", "sess-1"),
        ("issue", "#42")]
    assert found[0].raw == "@file:src/main.py"
    assert found[3].raw == "@url:https://example.com/docs"
    assert found[0].source == "prompt text"
    assert "true text" in found[0].reason


def test_parse_bare_form_is_the_shipped_file_form():
    found = parse_mentions(
        "Look at @src/main.py and @docs/guide.md, "
        "then @src/main.py again.")
    assert [(m.kind, m.target, m.raw) for m in found] == [
        ("file", "src/main.py", "@src/main.py"),
        ("file", "docs/guide.md", "@docs/guide.md")]
    # The bare form and the typed form name one pull once.
    both = parse_mentions("@src/main.py and @file:src/main.py")
    assert len(both) == 1
    assert both[0].raw == "@src/main.py"
    # Sentence punctuation rides no target.
    tail = parse_mentions("See @file:a/b.py.")
    assert tail[0].target == "a/b.py"
    assert tail[0].raw == "@file:a/b.py"


def test_parse_refusals_are_plain():
    with pytest.raises(ValueError) as excinfo:
        parse_mentions("hey @bogus:thing")
    assert "file/folder/symbol/url/image/session/issue" in str(
        excinfo.value)
    with pytest.raises(ValueError):
        parse_mentions("hey @file:")
    with pytest.raises(ValueError):
        parse_mentions("hey @file:  next")
    with pytest.raises(ValueError):
        parse_mentions("a @url:notaurl here")
    with pytest.raises(ValueError):
        parse_mentions(42)


def test_parse_mention_single():
    one = parse_mention("only @symbol:TokenEstimator here")
    assert one.kind == "symbol"
    assert parse_mentions("no mentions at all") == ()
    with pytest.raises(ValueError):
        parse_mention("no mentions at all")
    with pytest.raises(ValueError):
        parse_mention("@file:a.py and @file:b.py")


def test_format_mention_text_is_canonical():
    bare = parse_mention("@src/main.py")
    assert format_mention_text(bare) == "@file:src/main.py"
    typed = parse_mention("@issue:#42")
    assert format_mention_text(typed) == "@issue:#42"
    assert format_mention_text(_mention()) == (
        "@file:mythic_agent/core/context_budget.py")


def test_derive_plan_names_the_shipped_roads():
    for entry in load_mentions().mentions:
        plan = derive_plan(entry)
        assert isinstance(plan, MentionPlan)
        assert plan.mention_id == entry.mention_id
        assert plan.road == MENTION_ROADS[entry.kind]
        assert plan.action and plan.pulls
    plan = derive_plan(_mention())
    assert "ExplicitFilesSource" in plan.road
    assert plan.pulls == "The file's text, as one context block"


def test_validate_plan_judged_against_its_mention():
    entry = _mention()
    plan = derive_plan(entry)
    assert validate_plan(_plan_mapping(plan), entry) == plan
    assert build_plan(plan) == plan
    forged = _plan_mapping(plan)
    forged["road"] = "some invented road"
    with pytest.raises(ValueError):
        validate_plan(forged, entry)
    with pytest.raises(ValueError):
        validate_plan({**_plan_mapping(plan), "extra": 1}, entry)
    with pytest.raises(ValueError):
        validate_plan({"kind": "file"}, entry)


def test_derive_index_counts_in_first_appearance_order():
    index = derive_index(_mentions())
    assert index.total_mentions == 4
    assert [(c.kind, c.mentions) for c in index.kind_counts] == [
        ("file", 2), ("symbol", 1), ("issue", 1)]
    assert [r.mention_id for r in index.rows] == [
        e.mention_id for e in _mentions()]
    assert index.account[0] == (
        "The canon holds 4 mention(s): file 2, symbol 1, issue 1.")
    with pytest.raises(ValueError):
        derive_index([])


def test_validate_index_judged_against_its_mentions():
    entries = _mentions()
    index = derive_index(entries)
    assert validate_index(_index_mapping(index), entries) == index
    forged = _index_mapping(index)
    forged["account"] = ["A forged account."]
    with pytest.raises(ValueError):
        validate_index(forged, entries)
    with pytest.raises(ValueError):
        validate_index({**_index_mapping(index), "extra": 1}, entries)


def test_index_internal_inconsistency_refuses():
    entries = _mentions()
    index = derive_index(entries)
    bad_total = _index_mapping(index)
    bad_total["total_mentions"] = 99
    with pytest.raises(ValueError):
        validate_index(bad_total)
    bad_counts = _index_mapping(index)
    bad_counts["kind_counts"] = [
        {"kind": "file", "mentions": 9},
        {"kind": "symbol", "mentions": 1},
        {"kind": "issue", "mentions": 1}]
    bad_counts["total_mentions"] = 11
    with pytest.raises(ValueError):
        validate_index(bad_counts)


def test_book_validation_refusals():
    raw = yaml.safe_load(
        (ROOT / "mythic_agent" / "data" / "mentions.yaml").read_text(
            encoding="utf-8"))
    dup = dict(raw)
    dup["entries"] = list(raw["entries"]) + [dict(raw["entries"][0])]
    with pytest.raises(ValidationError):
        validate_book(dup)
    wrong_schema = dict(raw)
    wrong_schema["schema"] = "mythic.other/1"
    with pytest.raises(ValidationError):
        validate_book(wrong_schema)
    unknown = dict(raw)
    unknown["surprise"] = True
    with pytest.raises(ValidationError):
        validate_book(unknown)
    orphan_plan = dict(raw)
    orphan_plan["plans"] = [dict(raw["plans"][0], mention_id="mention-ghost")]
    with pytest.raises(ValidationError):
        validate_book(orphan_plan)
    forged_plan = dict(raw)
    forged_plan["plans"] = [
        dict(p, road="an invented road") if i == 0 else p
        for i, p in enumerate(raw["plans"])]
    with pytest.raises(ValidationError):
        validate_book(forged_plan)
    assert build_canon(raw).title == (
        "Mention canon at the M-147 slice boundary")
    with pytest.raises(ValidationError):
        validate_book(
            dict(raw, guide={"title": "Some other canon"}),
            require_example=True)


def test_load_mentions_file_roundtrip(tmp_path):
    raw = (ROOT / "mythic_agent" / "data" / "mentions.yaml").read_text(
        encoding="utf-8")
    path = tmp_path / "mentions.yaml"
    path.write_text(raw, encoding="utf-8")
    book = load_mentions_file(path)
    assert book.mention_ids() == load_mentions().mention_ids()
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: mythic.mentions/1\nentries: []\n",
                   encoding="utf-8")
    with pytest.raises(ValidationError):
        load_mentions_file(bad)
    with pytest.raises(FileNotFoundError):
        load_mentions_file(tmp_path / "missing.yaml")


def test_registry_holds_mentions_one_by_one():
    registry = MentionRegistry()
    with pytest.raises(ValueError):
        registry.canon()
    held = registry.register_mention({
        "kind": "file", "target": "a/b.py", "source": "s",
        "reason": "Named for the test."})
    assert held.mention_id == "mention-1"
    assert registry.get_mention("mention-1").target == "a/b.py"
    with pytest.raises(KeyError):
        registry.get_mention("mention-nope")
    with pytest.raises(ValueError):
        registry.register_mention({
            "kind": "file", "target": "a/b.py", "source": "s",
            "reason": "The same pull named twice."})
    with pytest.raises(ValueError):
        registry.register_mention(_mention())
        registry.register_mention(_mention())


def test_registry_canon_title_and_derivations():
    registry = MentionRegistry(load_mentions())
    assert registry.canon().title == (
        "Mention canon at the M-147 slice boundary")
    assert registry.plan_for("mention-issue-148").kind == "issue"
    assert registry.index().total_mentions == 7
    with pytest.raises(ValueError):
        registry.register_canon(build_canon(
            title="Another canon", mentions=_mentions()))


def test_records_and_plain_words():
    entry = _mention()
    record = mention_record(entry)
    assert record["type"] == "mentions_mention"
    assert record["news"] is True
    assert "@file:mythic_agent/core/context_budget.py" in (
        record["headline"])
    plan = derive_plan(entry)
    precord = plan_record(plan, entry)
    assert precord["type"] == "mentions_plan"
    assert "ExplicitFilesSource" in precord["headline"]
    index = derive_index(load_mentions())
    irecord = index_record(index, load_mentions())
    assert irecord["type"] == "mentions_index"
    assert "7 mention(s)" in irecord["headline"]
    brecord = book_record(load_mentions())
    assert brecord["type"] == "mentions_book"
    assert brecord["mention_count"] == 7
    assert "context_budget.py" in plain_words(entry)
    assert "runs nothing" in plan_plain_words(plan)
    words = index_plain_words(load_mentions())
    assert "Mention canon at the M-147 slice boundary" in words
    assert "@issue:#148" in words


def test_formatters_and_screen():
    book = load_mentions()
    line = format_mention(book.mentions[0])
    assert "mention-file-context-budget: file" in line
    only = format_mentions(book, "url")
    assert "mention-url-ast-docs" in only
    assert "mention-file-context-budget" not in only
    block = format_plan(derive_plan(book.mentions[1]))
    assert "Road:" in block and "build_repo_map" in block
    iblock = format_index(book)
    assert "Index in Mention canon at the M-147 slice boundary:" in iblock
    screen = format_mentions_screen(book)
    assert "The @-mention canon (M-148)" in screen
    assert USAGE in screen
    assert format_mentions_screen() == screen


def test_parse_mentions_args_grammar():
    assert parse_mentions_args("") == ("show", None)
    assert parse_mentions_args("show") == ("show", None)
    assert parse_mentions_args("list") == ("show", None)
    assert parse_mentions_args("index") == ("index", None)
    assert parse_mentions_args(
        "mention mention-file-context-budget") == (
            "mention", "mention-file-context-budget")
    assert parse_mentions_args("kind FILE") == ("kind", "file")
    assert parse_mentions_args(
        "plan mention-issue-148") == ("plan", "mention-issue-148")
    assert parse_mentions_args(
        "parse read @file:a/b.py now") == (
            "parse", "read @file:a/b.py now")
    for bad in ("dance party", "mention", "kind bogus",
                "plan", "parse", "index now"):
        with pytest.raises(ValueError) as excinfo:
            parse_mentions_args(bad)
        assert str(excinfo.value) == USAGE
    with pytest.raises(ValueError):
        parse_mentions_args(42)


def test_honest_boundary_parsing_and_planning_pull_nothing(tmp_path):
    # A mention naming a real file is parsed and
    # planned as data: the file's content stands
    # nowhere in the records, and no compiled
    # context changes - the pull happens only
    # through the shipped roads themselves, later.
    secret = tmp_path / "secret.py"
    secret.write_text("TOKEN = 'the-whole-file-text'\n",
                      encoding="utf-8")
    found = parse_mentions(f"read @file:{secret.name} please")
    assert len(found) == 1
    plan = derive_plan(found[0])
    blob = repr(found[0].to_record()) + repr(plan.to_record())
    assert "the-whole-file-text" not in blob
    assert not hasattr(found[0], "content")
    # The pure layer names roads as words: it
    # imports no pulling road at all.
    source = (ROOT / "mythic_agent" / "core" / "mentions.py").read_text(
        encoding="utf-8")
    for forbidden in ("from ..context", "from ..tools",
                      "import requests", "urlopen",
                      "from ..agents", "from ..ui"):
        assert forbidden not in source
    from mythic_agent.agents.context import ContextBuilder
    builder = ContextBuilder(max_tokens=4000)
    builder.add_system("You are the coder.")
    builder.add_turn("user", "Build the slice.")
    before = builder.build()
    parse_mentions("read @file:secret.py and @url:https://x.example")
    assert builder.build() == before


# -- agent layer -----------------------------------------------------------
#
# M-148 agent layer: the agent holds a
# MentionRegistry for the session (session state
# only, no new setting), mentions are held by
# being registered - published as their
# mention_record session news with the derived
# plan_record, and a whole canon's derived
# index_record, through the checkpoint road,
# deduped per id - the report road renders the
# held canon (or the shipped example when unheld)
# through the pure formatters, and the /mentions
# surface rides both roads on the pure parser +
# formatters. Status, get, kind, plan and index
# reads register and publish nothing, answer from
# the held registry first and from the shipped
# example only while nothing is held - a held
# session never falls back to the example. The
# plan and the index derive at call time from the
# held mentions, never held. This layer reads no
# file, fetches no page, compiles no context and
# persists nothing - and there is no Part VIII
# board yet, so the screen is where the canon is
# visible.

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _mention_events(store, session_id, kind):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == kind]


def _write_mentions_book(tmp_path):
    raw = (ROOT / "mythic_agent" / "data"
           / "mentions.yaml").read_text(encoding="utf-8")
    path = tmp_path / "mentions.yaml"
    path.write_text(raw, encoding="utf-8")
    return path


class TestMentionsAgentStatus:
    def test_status_starts_unheld_but_shows_the_example(self, agent):
        status = agent.mentions_status()
        assert status["mentions"] == []
        assert status["book"] is None
        assert status["mentions_canon"]["title"] == (
            "Mention canon at the M-147 slice boundary")
        assert [e["mention_id"]
                for e in status["mentions_canon"]["mentions"]] == [
            "mention-file-context-budget", "mention-folder-context",
            "mention-symbol-token-estimator", "mention-url-ast-docs",
            "mention-image-kiosk-snapshot", "mention-session-m147",
            "mention-issue-148"]
        assert status["book_record"]["type"] == "mentions_book"
        assert status["book_record"]["mention_count"] == 7
        assert len(status["plans"]) == 7
        assert status["plans"][0]["road"] == MENTION_ROADS["file"]
        assert status["index"]["total_mentions"] == 7
        assert [i["index_id"] for i in status["indexes"]] == [
            "index-m147-boundary"]
        assert "context_budget.py" in status["plain_words"][0]
        assert "runs nothing" in status["plan_plain_words"][0]
        assert "The @-mention canon:" in status["index_plain_words"]
        assert "The @-mention canon (M-148)" in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._mentions_registry() is agent._mentions_registry()
        assert agent._mentions_store is agent._mentions_registry()

    def test_reads_register_and_publish_nothing(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.mentions_status()
        entry = agent.get_mention("mention-file-context-budget")
        assert entry.kind == "file"
        plan = agent.mention_plan("mention-file-context-budget")
        assert plan.road == MENTION_ROADS["file"]
        index = agent.mentions_index()
        assert index.total_mentions == 7
        assert [e.mention_id for e in
                agent.mentions_for_kind("issue")] == ["mention-issue-148"]
        assert agent.mentions_canon().title == (
            "Mention canon at the M-147 slice boundary")
        registry = agent._mentions_registry()
        assert registry.list_mentions() == ()
        for kind in ("mentions_mention", "mentions_plan",
                     "mentions_index"):
            assert _mention_events(store, session_id, kind) == []
        agent.close()

    def test_unheld_reads_raise(self, agent):
        with pytest.raises(KeyError):
            agent.get_mention("mention-nope")
        with pytest.raises(KeyError):
            agent.mention_plan("mention-nope")

    def test_status_after_register_shows_the_held_pieces(self, agent):
        agent.register_mention(_mention())
        status = agent.mentions_status()
        assert [e["mention_id"] for e in status["mentions"]] == [
            "mention-file-context-budget"]
        assert status["book"]["mention_count"] == 1
        assert status["mentions_canon"]["title"] == (
            "Session mention canon")
        assert status["indexes"] == []
        assert status["index"]["total_mentions"] == 1
        assert "mention-file-context-budget" in status["screen"]

    def test_held_session_never_falls_back_to_the_example(self, agent):
        agent.register_mention(_mention())
        with pytest.raises(KeyError):
            agent.get_mention("mention-issue-148")
        assert agent.mentions_for_kind("issue") == ()
        assert agent.mentions_canon().mention_ids() == (
            "mention-file-context-budget",)
        assert agent.get_mention(
            "mention-file-context-budget").kind == "file"
        assert agent.mentions_index().total_mentions == 1
        assert agent.mention_plan(
            "mention-file-context-budget").kind == "file"


class TestMentionsAgentRegister:
    def test_register_mention_holds_and_publishes_once(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_mention(_mention())
        assert outcome["mention"]["mention_id"] == (
            "mention-file-context-budget")
        assert outcome["record"]["type"] == "mentions_mention"
        assert outcome["plan_record"]["type"] == "mentions_plan"
        events = _mention_events(store, session_id, "mentions_mention")
        assert len(events) == 1
        assert events[0]["mention_id"] == "mention-file-context-budget"
        plans = _mention_events(store, session_id, "mentions_plan")
        assert len(plans) == 1
        assert plans[0]["kind"] == "file"
        agent._publish_mentions_record(outcome["record"])
        agent._publish_mentions_record(outcome["plan_record"])
        assert len(_mention_events(
            store, session_id, "mentions_mention")) == 1
        assert len(_mention_events(
            store, session_id, "mentions_plan")) == 1
        from mythic_agent.core.context_budget import (
            book_record as _budget_book_record,
            load_context_budget,
        )
        from mythic_agent.core.crew_schedules import (
            attachment_record as _attachment_record,
            load_crew_schedules,
        )
        agent._publish_mentions_record(book_record(load_mentions()))
        agent._publish_mentions_record(_budget_book_record(
            load_context_budget()))
        agent._publish_mentions_record(_attachment_record(
            load_crew_schedules().entries[0]))
        for kind in ("mentions_book", "context_budget_book",
                     "crew_schedule_attachment"):
            assert _mention_events(store, session_id, kind) == []
        assert len(_mention_events(
            store, session_id, "mentions_mention")) == 1
        agent.close()

    def test_parse_and_register_publishes_the_pull(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.parse_and_register_mentions(
            "read @file:a/b.py and @symbol:TokenEstimator")
        assert outcome["count"] == 2
        assert [m["mention_id"] for m in outcome["mentions"]] == [
            "mention-1", "mention-2"]
        events = _mention_events(store, session_id, "mentions_mention")
        assert len(events) == 2
        assert agent.mentions_index().total_mentions == 2
        agent.close()

    def test_duplicate_mention_refuses_and_publishes_nothing_new(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_mention(_mention())
        with pytest.raises(ValueError):
            agent.register_mention(_mention())
        assert len(_mention_events(
            store, session_id, "mentions_mention")) == 1
        agent.close()

    def test_register_mention_without_id_gets_a_mention_id(self, agent):
        outcome = agent.register_mention({
            "kind": "issue", "target": "#7", "source": "a note",
            "reason": "Held for the session."})
        assert outcome["mention"]["mention_id"] == "mention-1"
        assert agent.get_mention("mention-1").kind == "issue"

    def test_register_canon_holds_and_publishes_in_order(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_mentions_canon(load_mentions())
        assert outcome["count"] == 7
        assert outcome["book"]["mention_count"] == 7
        events = _mention_events(store, session_id, "mentions_mention")
        assert [e["mention_id"] for e in events] == [
            "mention-file-context-budget", "mention-folder-context",
            "mention-symbol-token-estimator", "mention-url-ast-docs",
            "mention-image-kiosk-snapshot", "mention-session-m147",
            "mention-issue-148"]
        indexes = _mention_events(store, session_id, "mentions_index")
        assert len(indexes) == 1
        assert indexes[0]["total_mentions"] == 7
        assert agent.mentions_canon().title == (
            "Mention canon at the M-147 slice boundary")
        assert agent.mentions_canon().plans == ()
        assert agent.mentions_index().total_mentions == 7
        agent.close()

    def test_register_canon_twice_refuses(self, agent):
        agent.register_mentions_canon(load_mentions())
        with pytest.raises(ValueError):
            agent.register_mentions_canon(load_mentions())

    def test_record_canon_holds_and_publishes_the_example(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.record_mentions_canon()
        assert outcome["count"] == 7
        assert outcome["book"]["mention_count"] == 7
        events = _mention_events(store, session_id, "mentions_mention")
        assert [e["mention_id"] for e in events] == [
            "mention-file-context-budget", "mention-folder-context",
            "mention-symbol-token-estimator", "mention-url-ast-docs",
            "mention-image-kiosk-snapshot", "mention-session-m147",
            "mention-issue-148"]
        assert len(_mention_events(
            store, session_id, "mentions_index")) == 1
        assert agent.mentions_canon().title == (
            "Mention canon at the M-147 slice boundary")
        assert agent.mentions_canon().indexes[0].index_id == (
            "index-m147-boundary")
        assert agent.mentions_index().total_mentions == 7
        agent.close()

    def test_record_same_canon_twice_refuses(self, agent):
        agent.record_mentions_canon()
        with pytest.raises(ValueError):
            agent.record_mentions_canon()

    def test_book_from_a_file_is_recorded_at_the_agent_layer(
            self, agent, tmp_path):
        path = _write_mentions_book(tmp_path)
        book = load_mentions_file(path)
        outcome = agent.record_mentions_canon(book)
        assert outcome["count"] == 7
        assert agent.mentions_canon().title == (
            "Mention canon at the M-147 slice boundary")
        assert agent.get_mention("mention-issue-148").kind == "issue"
        assert agent.mentions_index().row_for(
            "mention-folder-context").kind == "folder"

    def test_one_by_one_holdings_stand_under_a_session_canon(self, agent):
        agent.register_mention(_mention())
        assert agent.mentions_canon().title == "Session mention canon"
        agent.register_mention(_mentions()[1])
        assert [e.mention_id
                for e in agent.mentions_canon().mentions] == [
            "mention-file-context-budget",
            "mention-symbol-token-estimator"]
        with pytest.raises(ValueError):
            agent.record_mentions_canon()


class TestMentionsAgentReport:
    def test_report_renders_the_example_when_unheld(self, agent):
        outcome = agent.report_mentions()
        assert outcome["book"]["title"] == (
            "Mention canon at the M-147 slice boundary")
        assert outcome["book"]["mention_count"] == 7
        assert "mention-issue-148" in outcome["mentions_text"]
        assert "The @-mention canon:" in outcome["index_text"]
        assert "The @-mention canon (M-148)" in outcome["screen"]
        assert outcome["explanation"] == PLAIN_EXPLANATION

    def test_report_renders_the_held_canon_only(self, agent):
        agent.register_mention(_mention())
        outcome = agent.report_mentions()
        assert outcome["book"]["mention_count"] == 1
        assert "mention-file-context-budget" in outcome["mentions_text"]
        assert "mention-issue-148" not in outcome["mentions_text"]
        assert "mention-issue-148" not in outcome["index_text"]

    def test_report_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.report_mentions()
        registry = agent._mentions_registry()
        assert registry.list_mentions() == ()
        for kind in ("mentions_mention", "mentions_plan",
                     "mentions_index"):
            assert _mention_events(store, session_id, kind) == []
        agent.close()

    def test_no_live_read_fetch_compile_or_persist_road(self, agent):
        # This layer holds the grammar as data: it
        # reads no file, fetches no page, compiles
        # no context, persists nothing - and there
        # is no Part VIII board yet. Holding a canon
        # changes no live context assembly: a
        # ContextBuilder's built messages are the
        # same before and after a canon is held.
        assert not hasattr(agent, "pull_mention")
        assert not hasattr(agent, "fetch_mention")
        assert not hasattr(agent, "persist_mentions")
        assert not hasattr(agent, "mentions_board")
        from mythic_agent.agents.context import ContextBuilder
        builder = ContextBuilder(max_tokens=4000)
        builder.add_system("You are the coder.")
        builder.add_turn("user", "Build the slice.")
        before = builder.build()
        agent.record_mentions_canon()
        assert builder.build() == before


class TestMentionsTerminalSurface:
    def test_show_mention_kind_plan_parse_and_index(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/mentions")
        assert "The @-mention canon (M-148)" in text
        _, _, text = _slash(
            agent, "/mentions mention mention-file-context-budget")
        assert "mention-file-context-budget: file" in text
        _, _, text = _slash(agent, "/mentions kind file")
        assert "mention-file-context-budget" in text
        assert "mention-issue-148" not in text
        _, _, text = _slash(agent, "/mentions plan mention-issue-148")
        assert "issue_slice" in text
        _, _, text = _slash(
            agent, "/mentions parse read @file:a/b.py please")
        assert "file - a/b.py" in text
        # Parsing on this surface holds nothing.
        assert agent._mentions_registry().list_mentions() == ()
        _, _, text = _slash(agent, "/mentions index")
        assert "The @-mention canon:" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert ("/mentions [show|mention <mention-id>|"
                "kind <kind>|plan <mention-id>|"
                "parse <text>|index]") in text
        _, _, text = _slash(agent, "/mentions dance party")
        assert text == USAGE
        _, _, text = _slash(agent, "/mentions mention mention-nope")
        assert "no mention in the canon" in text


@pytest.fixture()
def mentions_handler(agent, monkeypatch):
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


def _mentions_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestMentionsCommand:
    def test_show_is_default(self, mentions_handler, agent):
        mentions_handler._handle_mentions("")
        assert "The @-mention canon (M-148)" in (
            _mentions_published_text(mentions_handler))

    def test_mention_kind_plan_parse_and_index(
            self, mentions_handler, agent):
        mentions_handler._handle_mentions(
            "mention mention-file-context-budget")
        assert "context_budget.py" in _mentions_published_text(
            mentions_handler)
        mentions_handler._handle_mentions("kind issue")
        assert "mention-issue-148" in _mentions_published_text(
            mentions_handler)
        mentions_handler._handle_mentions("plan mention-issue-148")
        assert "issue_slice" in _mentions_published_text(
            mentions_handler)
        mentions_handler._handle_mentions("index")
        assert "The @-mention canon:" in _mentions_published_text(
            mentions_handler)

    def test_bad_grammar_is_published(self, mentions_handler, agent):
        mentions_handler._handle_mentions("dance party")
        assert USAGE in _mentions_published_text(mentions_handler)


class TestChatScreenRoutingMentions:
    def test_mentions_routes_as_system_command(self, monkeypatch):
        from mythic_agent.ui.screens import chat_screen
        from mythic_agent.ui.screens.chat_screen import MainChatScreen

        class _FakeLog:
            def __init__(self):
                self.lines = []

            def write(self, *args, **kwargs):
                self.lines.append(" ".join(str(a) for a in args))

        calls = []
        monkeypatch.setattr(
            chat_screen.SecureAPI, "publish_system_command",
            staticmethod(lambda cmd, args: calls.append((cmd, args))))
        screen = MainChatScreen.__new__(MainChatScreen)
        screen.handle_command(
            "/mentions mention mention-file-context-budget", _FakeLog())
        assert calls == [
            ("/mentions", "mention mention-file-context-budget")]
