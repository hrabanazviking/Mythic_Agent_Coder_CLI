"""M-121 Agents as files - pure-layer tests.

TIER: integration

The pure layer is the crew as data: a crew member
(name, office, model route, tools, posture,
character) validated as data, the shipped casting
(the existing characters as the first castings)
held in a data file, a loader that reads a casting
from any file so a new member is a file and not a
code change, a member record shaped as session
news, and a registry with deterministic ids.
Nothing here spawns an agent or runs a model.
"""

from pathlib import Path

import pytest

from mythic_agent.constants import DEFAULT_SUBAGENTS
from mythic_agent.core.crew_members import (
    CREW_RESOURCE,
    CREW_SCHEMA,
    CREW_SLICE,
    PLAIN_EXPLANATION,
    POSTURES,
    USAGE,
    Casting,
    CrewMember,
    CrewRegistry,
    CrewRoute,
    build_member,
    casting_record,
    format_crew_screen,
    format_member,
    format_members,
    load_casting,
    load_casting_file,
    member_offices,
    normalize_member_id,
    normalize_office,
    normalize_posture,
    parse_crew_args,
    plain_words,
    validate_casting,
    validate_member,
)
from mythic_agent.core.permission_profiles import BUILTIN_PROFILE_IDS
from mythic_agent.core.role_routing import office_for_agent_name, office_ids
from mythic_agent.core.tool_schemas import get_agent_tools
from mythic_agent.core.validation import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def _member(**kwargs):
    kwargs.setdefault("name", "Keeper - Testa Próf")
    kwargs.setdefault("office", "auditor")
    kwargs.setdefault("tools", ["read_file", "grep_search"])
    kwargs.setdefault("posture", "read-only-scout")
    kwargs.setdefault("character", "default_agent_characters/Testa.md")
    return CrewMember(**kwargs)


# -- constants and word readings --------------------------------------------


def test_constants_and_usage():
    assert CREW_SLICE == "M-121"
    assert CREW_SCHEMA == "mythic.crew_members/1"
    assert CREW_RESOURCE == "crew_members.yaml"
    assert POSTURES == BUILTIN_PROFILE_IDS
    assert USAGE.startswith("Usage: /crew")
    assert "office" in USAGE
    assert "file, not code" in PLAIN_EXPLANATION
    assert "first castings" in PLAIN_EXPLANATION


def test_offices_are_the_role_routing_offices_minus_primary():
    assert member_offices() == tuple(
        o for o in office_ids() if o != "primary")
    assert len(member_offices()) == 8


def test_word_readings():
    assert normalize_office("Forge-Worker") == "forge_worker"
    assert normalize_office(" ARCHITECT ") == "architect"
    assert normalize_posture("Read_Only_Scout") == "read-only-scout"
    assert normalize_member_id("crew-1") == "crew-1"
    for bad in ("primary", "Primary", "captain", "", None, 4):
        with pytest.raises(ValueError):
            normalize_office(bad)
    for bad in ("loose", "", None):
        with pytest.raises(ValueError):
            normalize_posture(bad)
    for bad in ("", "two words", None, 4):
        with pytest.raises(ValueError):
            normalize_member_id(bad)


# -- the shipped casting: the existing characters, as data -------------------


def test_shipped_casting_loads_and_is_complete():
    casting = load_casting()
    assert isinstance(casting, Casting)
    assert len(casting.members) == 8
    assert casting.casting_note
    rebuilt = {"schema": CREW_SCHEMA, "slice": CREW_SLICE,
               "members": [{
                   "id": m.member_id, "name": m.name,
                   "office": m.office, "model_route": None,
                   "tools": list(m.tools), "posture": m.posture,
                   "character": m.character}
                   for m in casting.members]}
    assert validate_casting(rebuilt, require_complete=True) == []


def test_casting_names_are_exactly_the_shipped_subagents():
    casting = load_casting()
    assert [m.name for m in casting.members] == [
        entry["name"] for entry in DEFAULT_SUBAGENTS]


def test_casting_offices_match_the_role_routing_mapping():
    casting = load_casting()
    for member in casting.members:
        assert office_for_agent_name(member.name) == member.office
        assert member.member_id == member.office


def test_casting_character_files_exist():
    casting = load_casting()
    for member in casting.members:
        assert (ROOT / member.character).is_file(), member.character


def test_casting_tools_are_shipped_tool_names():
    shipped = {t["function"]["name"] for t in get_agent_tools()}
    casting = load_casting()
    for member in casting.members:
        assert member.tools
        assert set(member.tools) <= shipped, member.name


def test_casting_routes_are_the_honest_session_default():
    # role_routes ships empty: no office holds an explicit
    # route, so every casting names the session default.
    casting = load_casting()
    assert all(m.model_route is None for m in casting.members)
    assert all(m.route_words == "the session default"
               for m in casting.members)


def test_casting_lookup_roads():
    casting = load_casting()
    architect = casting.by_office("architect")
    assert architect.name.startswith("Architect")
    assert casting.get("architect") is architect
    assert casting.by_name(architect.name) is architect
    with pytest.raises(KeyError):
        casting.get("nobody")
    with pytest.raises(ValueError):
        casting.by_office("primary")


# -- construction validation --------------------------------------------------


def test_member_defaults_and_record():
    member = _member()
    assert member.member_id is None
    assert member.model_route is None
    record = member.to_record()
    assert record["type"] == "crew_member"
    assert record["slice"] == "M-121"
    assert record["tools"] == ["read_file", "grep_search"]
    assert record["model_route"] is None


def test_member_with_explicit_route():
    member = _member(model_route={"model": "deep-1",
                                  "base_url": "http://x.invalid/v1"})
    assert isinstance(member.model_route, CrewRoute)
    assert member.route_words == "deep-1 at http://x.invalid/v1"
    assert member.to_record()["model_route"] == {
        "model": "deep-1", "base_url": "http://x.invalid/v1"}


def test_member_refusals():
    with pytest.raises(ValueError):
        _member(name="  ")
    with pytest.raises(ValueError):
        _member(name="x" * 121)
    with pytest.raises(ValueError):
        _member(office="primary")
    with pytest.raises(ValueError):
        _member(office="captain")
    with pytest.raises(ValueError):
        _member(posture="loose")
    with pytest.raises(ValueError):
        _member(character="")
    with pytest.raises(ValueError):
        _member(tools=[])
    with pytest.raises(ValueError):
        _member(tools="read_file")
    with pytest.raises(ValueError):
        _member(tools=["read_file", "read_file"])
    with pytest.raises(ValueError):
        _member(tools=["read file"])
    with pytest.raises(ValueError):
        _member(model_route={"model": "only-a-model"})
    with pytest.raises(ValueError):
        _member(model_route={"model": "m", "base_url": "u",
                             "provider": "p"})
    with pytest.raises(ValueError):
        _member(model_route="a-model-name")


def test_validate_member_mapping_and_aliases():
    member = validate_member({
        "id": "auditor", "name": "A", "office": "Auditor",
        "route": None, "tools": ["read_file"],
        "posture": "read-only-scout", "character": "c.md"})
    assert member.member_id == "auditor"
    assert member.office == "auditor"
    same = validate_member({
        "member_id": "auditor", "id": "auditor", "name": "A",
        "office": "auditor", "tools": ["read_file"],
        "posture": "read-only-scout", "character": "c.md"})
    assert same.member_id == "auditor"
    with pytest.raises(ValueError):
        validate_member({
            "member_id": "one", "id": "two", "name": "A",
            "office": "auditor", "tools": ["read_file"],
            "posture": "read-only-scout", "character": "c.md"})
    with pytest.raises(ValueError):
        validate_member({
            "name": "A", "office": "auditor", "tools": ["read_file"],
            "posture": "read-only-scout", "character": "c.md",
            "prompt": "prose does not live in the record"})
    with pytest.raises(ValueError):
        validate_member({"name": "A", "office": "auditor"})
    with pytest.raises(ValueError):
        validate_member("not a mapping")
    built = build_member(name="B", office="skald",
                         tools=["read_file"], posture="trusted-forge",
                         character="b.md")
    assert built.office == "skald"


# -- casting validation --------------------------------------------------------


def _casting_data(members):
    return {"schema": CREW_SCHEMA, "slice": CREW_SLICE,
            "members": members}


def _member_data(**kwargs):
    data = {"name": "New - Nýja Próf", "office": "skald",
            "tools": ["read_file"], "posture": "read-only-scout",
            "character": "new.md"}
    data.update(kwargs)
    return data


def test_validate_casting_refusals():
    assert validate_casting(_casting_data([_member_data()])) == []
    problems = validate_casting({"schema": "other/9",
                                 "slice": "M-999", "members": []})
    assert len(problems) == 3
    dup = _casting_data([_member_data(), _member_data()])
    assert any("held twice" in p or "duplicate" in p
               for p in validate_casting(dup))
    incomplete = validate_casting(
        _casting_data([_member_data()]), require_complete=True)
    assert any("no member holds the office" in p for p in incomplete)
    assert validate_casting("nope") == [
        "a casting must be a mapping, got 'nope'"]
    with pytest.raises(ValidationError):
        load_casting({"schema": "other/9", "slice": CREW_SLICE,
                      "members": [_member_data()]})


# -- new members are files, not code -------------------------------------------


def test_new_member_loads_from_a_temp_file(tmp_path):
    path = tmp_path / "extra_crew.yaml"
    path.write_text(
        "schema: mythic.crew_members/1\n"
        "slice: M-121\n"
        "members:\n"
        "- id: veilleur\n"
        "  name: \"Veilleur - Brandr Vakt\"\n"
        "  office: cartographer\n"
        "  model_route: null\n"
        "  tools: [read_file, grep_search]\n"
        "  posture: read-only-scout\n"
        "  character: \"default_agent_characters/Veilleur.md\"\n",
        encoding="utf-8")
    casting = load_casting_file(path)
    assert len(casting.members) == 1
    member = casting.get("veilleur")
    assert member.office == "cartographer"
    assert member.model_route is None


def test_temp_file_with_explicit_route_loads(tmp_path):
    path = tmp_path / "routed.yaml"
    path.write_text(
        "schema: mythic.crew_members/1\n"
        "slice: M-121\n"
        "members:\n"
        "- name: \"Routed - Runa Mark\"\n"
        "  office: architect\n"
        "  model_route: {model: deep-1, base_url: 'http://x.invalid/v1'}\n"
        "  tools: [read_file]\n"
        "  posture: trusted-forge\n"
        "  character: \"routed.md\"\n",
        encoding="utf-8")
    member = load_casting_file(path).members[0]
    assert member.route_words == "deep-1 at http://x.invalid/v1"


def test_temp_file_refusals(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_casting_file(missing)
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "schema: mythic.crew_members/1\nslice: M-121\nmembers:\n"
        "- {name: X, office: captain, tools: [read_file], "
        "posture: read-only-scout, character: x.md}\n",
        encoding="utf-8")
    with pytest.raises(ValidationError):
        load_casting_file(bad)
    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("members: [unclosed\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_casting_file(malformed)


# -- the registry ----------------------------------------------------------------


def test_registry_deterministic_ids():
    registry = CrewRegistry()
    first = registry.register(_member(name="One - Fyrsta"))
    second = registry.register(_member(name="Two - Önnur"))
    assert (first.member_id, second.member_id) == ("crew-1", "crew-2")
    named = registry.register(_member(member_id="crew-3",
                                      name="Three - Þriðja"))
    assert named.member_id == "crew-3"
    fourth = registry.register(_member(name="Four - Fjórða"))
    assert fourth.member_id == "crew-4"
    assert registry.get("crew-2") is second
    assert [m.member_id for m in registry.list_members()] == [
        "crew-1", "crew-2", "crew-3", "crew-4"]
    assert registry.list_members("auditor") == registry.list_members()
    assert registry.list_members("skald") == ()
    with pytest.raises(KeyError):
        registry.get("crew-99")


def test_registry_refuses_duplicates():
    registry = CrewRegistry()
    registry.register(_member(member_id="fixed", name="Same Name"))
    with pytest.raises(ValueError):
        registry.register(_member(member_id="fixed", name="Other"))
    with pytest.raises(ValueError):
        registry.register(_member(name="Same Name"))


def test_registry_holds_the_shipped_casting():
    registry = CrewRegistry()
    held = registry.register_casting(load_casting())
    assert len(held) == 8
    assert registry.get("guardian").name == "Thor Guardian"
    with pytest.raises(ValueError):
        registry.register_casting("not a casting")


# -- records, plain words, formatters, parser -------------------------------------


def test_casting_record_is_session_news():
    member = _member(member_id="auditor")
    record = casting_record(member)
    assert record["type"] == "crew_member"
    assert record["news"] is True
    assert record["member_id"] == "auditor"
    assert record["headline"] == plain_words(member)
    assert "auditor office" in record["headline"]


def test_plain_words_and_formatters():
    member = _member(member_id="auditor")
    words = plain_words(member)
    assert words.startswith("Keeper - Testa Próf holds the auditor office")
    assert "posture read-only-scout" in words
    assert "session default" in words
    assert format_member(member).startswith("  auditor: ")
    empty = format_members()
    assert empty.startswith("Crew members: none.")
    listed = format_members([member])
    assert listed.startswith("Crew members: 1 held.")
    assert format_members(load_casting()).startswith(
        "Crew members: 8 held.")
    screen = format_crew_screen(load_casting())
    assert "Agents as files (M-121)" in screen
    assert "Crew members: 8 held." in screen
    assert USAGE in screen
    with pytest.raises(ValueError):
        format_members("not a list")


def test_parse_crew_args():
    assert parse_crew_args("") == ("show", None)
    assert parse_crew_args(None) == ("show", None)
    assert parse_crew_args("show") == ("show", None)
    assert parse_crew_args("list") == ("show", None)
    assert parse_crew_args("show architect") == ("show", "architect")
    assert parse_crew_args("architect") == ("show", "architect")
    assert parse_crew_args("office Forge-Worker") == (
        "office", "forge_worker")
    for bad in ("show a b", "office", "office primary", "add x",
                "show two words", 4):
        with pytest.raises(ValueError):
            parse_crew_args(bad)


# -- purity ------------------------------------------------------------------------


def test_module_purity():
    source = (ROOT / "mythic_agent" / "core" /
              "crew_members.py").read_text(encoding="utf-8")
    body = source.split('"""', 2)[2]
    assert "agents.llm" not in body
    assert "agents.command_handler" not in body
    assert "ui.screens" not in body
    assert "subprocess" not in body
    assert "AgentManager" not in body
    assert "spawn_subagent" not in body


# -- agent layer -----------------------------------------------------------
#
# M-121 agent layer: the agent holds a CrewRegistry
# for the session (session state only, no new
# setting), a member joins by being registered or by
# a casting being loaded - published as its
# casting_record session news through the checkpoint
# road, deduped per member id - and a held member
# spawns from its record through the one shipped
# road (AgentManager.spawn_subagent, fed the
# member's name, its M-029 office route and its
# record's posture). The /crew surface rides both
# roads on the pure parser + formatters.

import copy as _copy

from mythic_agent.core.sessions import SessionStore as _SessionStore


def _crew_events(store, session_id):
    return [e for e in store.export(session_id)["events"]
            if e["type"] == "crew_member"]


def _forget_crew_thread(name):
    from mythic_agent.core.thread_audit import THREAD_REGISTRY
    THREAD_REGISTRY.forget(f"mythic-subagent-loop:{name}")


def _spawn_env(agent, monkeypatch):
    from unittest.mock import Mock

    from mythic_agent.agents import llm
    monkeypatch.setattr(llm.config_manager, "load_config",
                        lambda: _copy.deepcopy(agent.config))
    monkeypatch.setattr(llm, "AGENT_REGISTRY", {})
    monkeypatch.setattr(llm.threading, "Thread", Mock())
    return llm


class TestCrewAgentStatus:
    def test_status_starts_unheld_but_shows_the_casting(self, agent):
        status = agent.crew_status()
        assert status["members"] == []
        assert [m["name"] for m in status["casting"]] == [
            entry["name"] for entry in DEFAULT_SUBAGENTS]
        assert "Crew members: 8 held." in status["screen"]
        assert status["explanation"] == PLAIN_EXPLANATION

    def test_registry_is_one_per_agent(self, agent):
        assert agent._crew_registry() is agent._crew_registry()
        assert agent._crew_store is agent._crew_registry()

    def test_status_read_registers_and_publishes_nothing(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.crew_status()
        assert agent._crew_registry().list_members() == ()
        assert _crew_events(store, session_id) == []
        agent.close()

    def test_unknown_member_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.get_crew_member("crew-99")

    def test_status_after_register_shows_the_held_member(self, agent):
        agent.register_crew_member(_member())
        status = agent.crew_status()
        assert [m["member_id"] for m in status["members"]] == ["crew-1"]
        assert "Crew members: 1 held." in status["screen"]
        assert len(status["casting"]) == 8


class TestCrewAgentRegister:
    def test_register_holds_and_publishes_once(self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.register_crew_member(_member())
        assert outcome["member"]["member_id"] == "crew-1"
        assert outcome["record"]["type"] == "crew_member"
        assert outcome["record"]["news"] is True
        assert agent.get_crew_member("crew-1").name == (
            "Keeper - Testa Próf")
        events = _crew_events(store, session_id)
        assert len(events) == 1
        assert events[0]["member_id"] == "crew-1"
        # Deduped per record id: a second publish is no second event.
        agent._publish_crew_record(outcome["record"])
        assert len(_crew_events(store, session_id)) == 1
        # A foreign record type is never published on this road.
        agent._publish_crew_record({"type": "project_policy"})
        assert len(_crew_events(store, session_id)) == 1
        agent.close()

    def test_register_duplicate_refuses_and_holds_nothing_new(
            self, agent):
        agent.register_crew_member(_member(member_id="fixed"))
        with pytest.raises(ValueError):
            agent.register_crew_member(
                _member(member_id="fixed", name="Other - Önnur"))
        assert len(agent._crew_registry().list_members()) == 1

    def test_load_crew_casting_holds_and_publishes_the_eight(
            self, agent, tmp_path):
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        outcome = agent.load_crew_casting()
        assert outcome["count"] == 8
        assert [m["member_id"] for m in outcome["members"]] == [
            m.office for m in load_casting().members]
        assert agent.get_crew_member("guardian").name == "Thor Guardian"
        status = agent.crew_status()
        assert len(status["members"]) == 8
        assert "Crew members: 8 held." in status["screen"]
        events = _crew_events(store, session_id)
        assert len(events) == 8
        assert {e["member_id"] for e in events} == set(member_offices())
        with pytest.raises(ValueError):
            agent.load_crew_casting()
        agent.close()

    def test_new_member_joins_from_a_file_at_the_agent_layer(
            self, agent, tmp_path):
        path = tmp_path / "extra_crew.yaml"
        path.write_text(
            "schema: mythic.crew_members/1\n"
            "slice: M-121\n"
            "members:\n"
            "- id: veilleur\n"
            "  name: \"Veilleur - Brandr Vakt\"\n"
            "  office: cartographer\n"
            "  model_route: null\n"
            "  tools: [read_file, grep_search]\n"
            "  posture: read-only-scout\n"
            "  character: \"default_agent_characters/Veilleur.md\"\n",
            encoding="utf-8")
        outcome = agent.load_crew_casting(load_casting_file(path))
        assert outcome["count"] == 1
        assert agent.get_crew_member("veilleur").office == "cartographer"

    def test_find_and_office_roads_fall_back_to_the_casting(self, agent):
        found = agent.find_crew_member("architect")
        assert found.name.startswith("Architect")
        holder = agent.crew_member_for_office("skald")
        assert holder.member_id == "skald"
        with pytest.raises(KeyError):
            agent.find_crew_member("nobody")
        with pytest.raises(ValueError):
            agent.crew_member_for_office("primary")
        # A held member answers before the casting does.
        agent.register_crew_member(_member(
            member_id="my-auditor", name="Mine - Mín Próf"))
        assert agent.crew_member_for_office("auditor").member_id == (
            "my-auditor")


class TestCrewAgentSpawn:
    def test_spawn_rides_the_shipped_road_with_the_records_posture(
            self, agent, monkeypatch):
        llm = _spawn_env(agent, monkeypatch)
        agent.load_crew_casting()
        member = agent.get_crew_member("architect")
        _forget_crew_thread(member.name)
        outcome = agent.spawn_crew_member(
            "architect", task="Map the new module.")
        child = llm.AGENT_REGISTRY.get(member.name)
        try:
            assert outcome["spawned"] is True
            assert outcome["agent_name"] == member.name
            assert child is not None
            # read-only-scout rides as the read-only policy mode.
            assert outcome["policy_mode"] == "read-only"
            assert child.tool_policy.mode == "read-only"
            assert outcome["route_words"] == "the session default"
            assert outcome["task_queued"] is True
            assert child.inbox.get_nowait() == (
                "Task from Primary:\nMap the new module.")
        finally:
            if child is not None:
                child.close()
            _forget_crew_thread(member.name)

    def test_spawn_forge_worker_rides_as_ask(self, agent, monkeypatch):
        llm = _spawn_env(agent, monkeypatch)
        agent.load_crew_casting()
        member = agent.get_crew_member("forge_worker")
        _forget_crew_thread(member.name)
        outcome = agent.spawn_crew_member("forge_worker")
        child = llm.AGENT_REGISTRY.get(member.name)
        try:
            assert outcome["spawned"] is True
            # trusted-forge asks first: the ask policy mode.
            assert outcome["policy_mode"] == "ask"
            assert child.tool_policy.mode == "ask"
            assert outcome["task_queued"] is False
            assert child.inbox.empty()
        finally:
            if child is not None:
                child.close()
            _forget_crew_thread(member.name)

    def test_spawn_applies_an_explicit_record_route(
            self, agent, monkeypatch):
        llm = _spawn_env(agent, monkeypatch)
        agent.register_crew_member(_member(
            member_id="routed-arch",
            name="Architect - Rúnhild Svartdóttir",
            office="architect",
            model_route={"model": "deep-1",
                         "base_url": "http://x.invalid/v1"}))
        name = "Architect - Rúnhild Svartdóttir"
        _forget_crew_thread(name)
        outcome = agent.spawn_crew_member("routed-arch")
        child = llm.AGENT_REGISTRY.get(name)
        try:
            assert outcome["spawned"] is True
            assert outcome["route_words"] == (
                "deep-1 at http://x.invalid/v1")
            assert child.config["model"] == "deep-1"
            assert child.config["base_url"] == "http://x.invalid/v1"
        finally:
            if child is not None:
                child.close()
            _forget_crew_thread(name)

    def test_spawn_publishes_the_casting_record_once(
            self, agent, tmp_path, monkeypatch):
        llm = _spawn_env(agent, monkeypatch)
        store = _SessionStore(tmp_path, tmp_path / "state")
        session_id = agent.attach_session(store)
        agent.register_crew_member(_member(
            member_id="arch", name="Architect - Rúnhild Svartdóttir",
            office="architect"))
        assert len(_crew_events(store, session_id)) == 1
        name = "Architect - Rúnhild Svartdóttir"
        _forget_crew_thread(name)
        outcome = agent.spawn_crew_member("arch")
        child = llm.AGENT_REGISTRY.get(name)
        try:
            assert outcome["spawned"] is True
            # Joining published once; spawning the same member
            # does not publish its record a second time.
            assert len(_crew_events(store, session_id)) == 1
        finally:
            if child is not None:
                child.close()
            _forget_crew_thread(name)
        agent.close()

    def test_spawn_unknown_member_raises_keyerror(self, agent):
        with pytest.raises(KeyError):
            agent.spawn_crew_member("crew-99")

    def test_member_from_a_file_alone_cannot_spawn(
            self, agent, monkeypatch):
        llm = _spawn_env(agent, monkeypatch)
        agent.register_crew_member(_member(
            member_id="veilleur", name="Veilleur - Brandr Vakt",
            office="cartographer"))
        outcome = agent.spawn_crew_member("veilleur")
        # The honest boundary: the spawn road only spawns names
        # the session config carries as sub-agent entries, and
        # this member's name is not one - no agent is invented.
        assert outcome["spawned"] is False
        assert "No sub-agent named" in outcome["reason"]
        assert "Veilleur - Brandr Vakt" not in llm.AGENT_REGISTRY


class TestCrewTerminalSurface:
    def test_show_one_and_office(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/crew")
        assert "Crew members: 8 held." in text
        _, _, text = _slash(agent, "/crew show architect")
        assert "architect:" in text and "Rúnhild" in text
        _, _, text = _slash(agent, "/crew office skald")
        assert "Sigrún" in text
        _, _, text = _slash(agent, "/crew nobody")
        assert "unknown crew member" in text

    def test_help_line_and_bad_grammar(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/help")
        assert "/crew [show|show <member>|office <office>]" in text
        _, _, text = _slash(agent, "/crew add x")
        assert text == USAGE

    def test_bare_member_id_shows_one(self, agent):
        from mythic_agent.terminal import _slash
        _, _, text = _slash(agent, "/crew guardian")
        assert "guardian:" in text and "Thor Guardian" in text


@pytest.fixture()
def crew_handler(agent, monkeypatch):
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


def _crew_published_text(handler):
    return "\n".join(kwargs.get("text", "")
                     for event, kwargs in handler.published
                     if event == "agent_chat_chunk")


class TestCrewCommand:
    def test_show_is_default(self, crew_handler, agent):
        crew_handler._handle_crew("")
        assert "Crew members: 8 held." in _crew_published_text(
            crew_handler)

    def test_show_one_and_office(self, crew_handler, agent):
        crew_handler._handle_crew("show guardian")
        assert "Thor Guardian" in _crew_published_text(crew_handler)
        crew_handler._handle_crew("office forge_worker")
        assert "Eldra" in _crew_published_text(crew_handler)

    def test_bad_grammar_is_published(self, crew_handler, agent):
        crew_handler._handle_crew("add x")
        assert "Usage: /crew" in _crew_published_text(crew_handler)

    def test_unknown_member_is_published(self, crew_handler, agent):
        crew_handler._handle_crew("show nobody")
        assert "unknown crew member" in _crew_published_text(crew_handler)


class TestCrewSpawnPostureModes:
    def test_every_shipped_posture_has_a_policy_mode(self, agent):
        from mythic_agent.core.permission_profiles import (
            builtin_profile,
            policy_mode_for,
        )
        for member in load_casting().members:
            mode = policy_mode_for(builtin_profile(member.posture))
            assert mode in ("read-only", "ask", "trusted")


class TestChatScreenRoutingCrew:
    def test_crew_routes_as_system_command(self, monkeypatch):
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
        screen.handle_command("/crew office skald", _FakeLog())
        assert calls == [("/crew", "office skald")]
