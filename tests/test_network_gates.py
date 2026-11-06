"""M-098 Network gates - pure-layer tests.

TIER: integration

The pure layer holds per-tool, per-domain
allowlists and decides outbound reaches
mechanically: allow needs an entry matching both
the tool and the host, everything else is refused
by default (fail-closed), malformed entries
refuse, and a refusal is shaped as news - a
session-event record with a plain headline -
never just a log line.

Domain rules pinned here: a plain domain matches
that host exactly (no subdomains); a ``*.``
domain matches subdomains at any depth but never
the base host itself.
"""

import pytest

from mythic_agent.core.network_gates import (
    ALLOWLIST_KEY,
    DECISIONS,
    DEFAULT_DECISION,
    NETWORK_GATES_SLICE,
    PLAIN_EXPLANATION,
    SETTING_KEY,
    AllowlistEntry,
    NetworkGates,
    build_allowlist,
    build_refusal,
    check_network,
    decide_network,
    enabled_from_config,
    entry_matches,
    extract_host,
    format_allowlist,
    format_gate_change,
    format_network_decision,
    format_network_gates,
    format_refusal,
    gates_from_config,
    normalize_domain_pattern,
    normalize_host,
    normalize_tool,
    parse_network_args,
    refusal_record,
    set_enabled,
    validate_entry,
)

ENTRIES = build_allowlist([
    {"tool": "curl", "domain": "example.com"},
    {"tool": "git", "domain": "*.github.com"},
    {"tool": "*", "domain": "pypi.org"},
])


# -- names and hosts ------------------------------------------------------


def test_tool_names_normalize_and_wildcard():
    assert normalize_tool(" Curl ") == "curl"
    assert normalize_tool("*") == "*"
    with pytest.raises(ValueError):
        normalize_tool("")
    with pytest.raises(ValueError):
        normalize_tool("bad tool!")
    with pytest.raises(ValueError):
        normalize_tool(None)


def test_extract_host_from_urls_and_bare_targets():
    assert extract_host("example.com") == "example.com"
    assert extract_host("https://Example.COM:8443/a/b?x=1") == "example.com"
    assert extract_host("http://user@example.com/path") == "example.com"
    assert extract_host("example.com:8080") == "example.com"
    assert extract_host("api.example.com.") == "api.example.com"
    assert extract_host("https://192.168.0.1:9000/x") == "192.168.0.1"


def test_extract_host_refuses_unreadable_targets():
    for bad in ("", "   ", "https://", "not a host", "exa_mple.com"):
        with pytest.raises(ValueError):
            extract_host(bad)
    with pytest.raises(ValueError):
        normalize_host("https://example.com")


def test_domain_patterns_normalize():
    assert normalize_domain_pattern("Example.COM.") == "example.com"
    assert normalize_domain_pattern("*.Example.com") == "*.example.com"
    assert normalize_host("LOCALHOST") == "localhost"


# -- entry validation -------------------------------------------------------


def test_validate_entry_forms_agree():
    from_dict = validate_entry({"tool": "Curl", "domain": "Example.com"})
    from_text = validate_entry("curl:example.com")
    from_obj = validate_entry(AllowlistEntry("curl", "example.com"))
    assert from_dict == from_text == from_obj == AllowlistEntry(
        "curl", "example.com")
    assert from_dict.to_record() == {"tool": "curl", "domain": "example.com"}


def test_malformed_entries_refuse():
    bad_specs = [
        {"tool": "curl"},
        {"domain": "example.com"},
        {"tool": "curl", "domain": "example.com", "extra": 1},
        {"tool": "", "domain": "example.com"},
        {"tool": "curl", "domain": ""},
        {"tool": "curl", "domain": "*"},
        {"tool": "curl", "domain": "*.*.example.com"},
        {"tool": "curl", "domain": "exa_mple.com"},
        {"tool": "curl", "domain": "-bad-.com"},
        "curl example.com",
        "curl:",
        42,
    ]
    for spec in bad_specs:
        with pytest.raises(ValueError):
            validate_entry(spec)


def test_build_allowlist_dedupes_and_refuses_wholesale():
    entries = build_allowlist([
        "curl:example.com", {"tool": "curl", "domain": "example.com"},
        "git:github.com"])
    assert entries == (AllowlistEntry("curl", "example.com"),
                       AllowlistEntry("git", "github.com"))
    assert build_allowlist(None) == ()
    assert build_allowlist([]) == ()
    with pytest.raises(ValueError):
        build_allowlist(["curl:example.com", {"tool": "x"}])
    with pytest.raises(ValueError):
        build_allowlist("curl:example.com")


# -- matching -----------------------------------------------------------------


def test_entry_matches_needs_tool_and_domain():
    entry = AllowlistEntry("curl", "example.com")
    assert entry_matches(entry, "curl", "example.com") is True
    assert entry_matches(entry, "wget", "example.com") is False
    assert entry_matches(entry, "curl", "other.com") is False


def test_plain_domain_is_exact_only():
    entry = AllowlistEntry("curl", "example.com")
    assert entry_matches(entry, "curl", "api.example.com") is False
    assert entry_matches(entry, "curl", "example.com.evil.com") is False
    assert entry_matches(entry, "curl", "notexample.com") is False


def test_wildcard_domain_matches_subdomains_not_apex():
    entry = AllowlistEntry("git", "*.github.com")
    assert entry_matches(entry, "git", "api.github.com") is True
    assert entry_matches(entry, "git", "a.b.github.com") is True
    assert entry_matches(entry, "git", "github.com") is False
    assert entry_matches(entry, "git", "github.com.evil.com") is False


def test_wildcard_tool_matches_any_tool():
    entry = AllowlistEntry("*", "pypi.org")
    assert entry_matches(entry, "pip", "pypi.org") is True
    assert entry_matches(entry, "curl", "pypi.org") is True
    assert entry_matches(entry, "pip", "files.pypi.org") is False


# -- the check ------------------------------------------------------------------


def test_check_allows_matching_tool_and_domain():
    decision = check_network("curl", "https://example.com/data", ENTRIES)
    assert decision.allowed is True and decision.decision == "allow"
    assert decision.host == "example.com"
    assert decision.matched_entry == AllowlistEntry("curl", "example.com")
    assert "allow" in DECISIONS and DEFAULT_DECISION == "deny"
    assert decision.to_record()["slice"] == NETWORK_GATES_SLICE == "M-098"


def test_check_is_per_tool():
    assert check_network("git", "https://api.github.com", ENTRIES).allowed
    denied = check_network("curl", "https://api.github.com", ENTRIES)
    assert denied.allowed is False
    assert denied.matched_entry is None
    assert "no allowlist entry" in denied.reason


def test_check_is_per_domain():
    assert check_network("pip", "https://pypi.org", ENTRIES).allowed
    denied = check_network("pip", "https://files.pypi.org", ENTRIES)
    assert denied.allowed is False and denied.host == "files.pypi.org"


def test_default_deny_with_empty_allowlist():
    decision = check_network("curl", "https://example.com")
    assert decision.allowed is False and decision.decision == "deny"
    assert "deny by default" in decision.reason
    assert NetworkGates().check("git", "github.com").allowed is False


def test_check_unreadable_target_is_refused_not_raised():
    decision = check_network("curl", "not a host", ENTRIES)
    assert decision.allowed is False and decision.host is None
    assert decision.reason.startswith("refused:")
    with pytest.raises(ValueError):
        check_network("bad tool!", "https://example.com", ENTRIES)


def test_decide_network_is_the_same_check():
    assert decide_network is check_network
    gates = NetworkGates(entries=ENTRIES)
    assert gates.check("curl", "example.com").allowed is True
    record = gates.to_record()
    assert record["default"] == "deny" and len(record["entries"]) == 3


# -- refusal as news --------------------------------------------------------------


def test_refusal_record_is_news_shaped():
    decision = check_network("curl", "https://evil.example", ENTRIES)
    record = refusal_record(decision, command="curl https://evil.example")
    assert record["type"] == "network_refusal"
    assert record["news"] is True
    assert record["surface"] == "session_event"
    assert record["tool"] == "curl" and record["host"] == "evil.example"
    assert record["command"] == "curl https://evil.example"
    assert "curl" in record["headline"] and "evil.example" in record["headline"]


def test_refusal_format_is_a_plain_headline():
    decision = check_network("wget", "https://example.com", ENTRIES)
    refusal = build_refusal(decision)
    text = format_refusal(refusal)
    assert text.startswith("Network refusal:")
    assert "wget" in text and "example.com" in text
    assert format_refusal(refusal.to_record()) == text
    assert format_network_decision(decision) == text + "."
    with pytest.raises(ValueError):
        format_refusal({"type": "something_else"})


def test_allowed_reach_has_no_refusal():
    decision = check_network("curl", "https://example.com", ENTRIES)
    with pytest.raises(ValueError):
        build_refusal(decision)
    allowed_text = format_network_decision(decision)
    assert allowed_text.startswith("Network allowed:")


# -- the gate -----------------------------------------------------------------------


def test_gate_defaults_on_and_reads_bool():
    assert SETTING_KEY == "network_gates"
    assert enabled_from_config({}) is True
    assert enabled_from_config({SETTING_KEY: False}) is False
    with pytest.raises(ValueError):
        enabled_from_config({SETTING_KEY: "yes"})


def test_gates_from_config_reads_the_allowlist():
    config = {ALLOWLIST_KEY: [{"tool": "curl", "domain": "example.com"}]}
    gates = gates_from_config(config)
    assert gates.check("curl", "example.com").allowed is True
    assert gates_from_config({}).entries == ()
    with pytest.raises(ValueError):
        gates_from_config({ALLOWLIST_KEY: [{"tool": "curl"}]})


def test_set_enabled_is_pure_and_names_noops():
    config = {}
    value, change = set_enabled(config, False)
    assert value is False and change.before is True and change.after is False
    assert config == {}  # pure: the caller's config is untouched
    assert change.event()["type"] == "network_gates_setting_changed"
    with pytest.raises(ValueError):
        set_enabled({}, True)  # already on
    with pytest.raises(ValueError):
        set_enabled({}, "off")


def test_format_gate_change_speaks_plainly():
    _, change = set_enabled({}, False)
    assert format_gate_change(change.record("s1", True)) == (
        "The network gates are now off.")


# -- the /network grammar --------------------------------------------------------------


def test_parse_show_gate_and_list():
    assert parse_network_args("") == {"action": "show"}
    assert parse_network_args("show") == {"action": "show"}
    assert parse_network_args("on") == {"action": "on"}
    assert parse_network_args("off") == {"action": "off"}
    assert parse_network_args("list") == {"action": "list"}


def test_parse_check_and_allow_forms():
    parsed = parse_network_args("check curl https://example.com/x")
    assert parsed == {"action": "check", "tool": "curl",
                      "target": "https://example.com/x"}
    decision = check_network(parsed["tool"], parsed["target"], ENTRIES)
    assert decision.allowed is True
    parsed = parse_network_args("allow git *.github.com")
    assert parsed == {"action": "allow",
                      "entry": {"tool": "git", "domain": "*.github.com"}}


def test_parse_refuses_unknown_grammar():
    for bad in ("frobnicate", "check curl", "check", "allow git",
                "allow git *", "allow bad!tool example.com"):
        with pytest.raises(ValueError):
            parse_network_args(bad)


# -- formatters ---------------------------------------------------------------------------


def test_format_allowlist_empty_and_entries():
    empty = format_allowlist(())
    assert "empty" in empty and "refused by default" in empty
    text = format_allowlist(ENTRIES)
    assert "curl: example.com" in text
    assert "git: *.github.com" in text
    assert "*: pypi.org" in text


def test_format_whole_slice():
    whole = format_network_gates({})
    assert "M-098" in whole and PLAIN_EXPLANATION in whole
    assert "Setting: on (network_gates)" in whole
    assert "Default posture: deny" in whole
    assert "Network refusal:" in whole  # the sample reach is refused
    off = format_network_gates({SETTING_KEY: False})
    assert "Setting: off (network_gates)" in off
    allowed = format_network_gates(
        {ALLOWLIST_KEY: [{"tool": "curl", "domain": "example.com"}]})
    assert "Network allowed:" in allowed
