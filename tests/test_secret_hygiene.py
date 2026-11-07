"""M-110 Secret hygiene in action - pure-layer tests.

TIER: integration

The pure layer is secret hygiene as data: the known
secret shapes held as validated data, a redaction
function that replaces a matched secret with one
fixed marker and never returns it, a file-screening
judge naming the file and the pattern kinds only
(content never in any record), a refusal record
shaped as session news, and a small registry with
deterministic ids. Nothing here writes a file, runs
a command or changes a setting.

Every secret below is FAKE and clearly synthetic,
invented for these tests - never a real credential.
"""

import pytest

from mythic_agent.core.secret_hygiene import (
    PLAIN_EXPLANATION,
    REDACTION_MARKER,
    SECRET_HYGIENE_SLICE,
    SECRET_KINDS,
    SECRET_PATTERNS,
    SCREENING_STATUSES,
    USAGE,
    FileScreening,
    HygieneRegistry,
    Screening,
    SecretPattern,
    build_pattern,
    build_screening,
    filename_kinds,
    format_hygiene_record,
    format_pattern,
    format_patterns,
    format_record,
    format_screening,
    format_screenings,
    format_secrets_screen,
    hygiene_record,
    normalize_hygiene_id,
    normalize_pattern_basis,
    normalize_secret_kind,
    normalize_screening_status,
    parse_secrets_args,
    pattern_for_kind,
    redact_secrets,
    screen_file,
    secret_kinds_in,
    validate_pattern,
    validate_screening,
)

FAKE_OPENAI = "sk-" + "FAKE0" * 8
FAKE_ANTHROPIC = "sk-ant-" + "FAKE1" * 8
FAKE_GITHUB = "ghp_" + "FAKE2" * 9
FAKE_AWS_ACCESS = "AKIA" + "FAKE3" * 3 + "F"
FAKE_STRIPE = "sk_live_" + "FAKE4" * 6
FAKE_SLACK = "xoxb-" + "1234567890" + "-" + "FAKE5" * 4
FAKE_GOOGLE = "AIza" + "FAKE6" * 7
FAKE_XAI = "xai-" + "FAKE7" * 8
FAKE_PRIVATE_HEADER = "-----BEGIN RSA PRIVATE KEY-----"
FAKE_GENERIC_LINE = 'api_key = "' + "FAKE8" * 6 + '"'


def _registry(*screenings):
    registry = HygieneRegistry()
    for screening in screenings:
        registry.register(screening)
    return registry


# -- constants, patterns and word readings ----------------------------


def test_constants_and_usage():
    assert SECRET_HYGIENE_SLICE == "M-110"
    assert SCREENING_STATUSES == ("clean", "refused")
    assert REDACTION_MARKER == "[REDACTED]"
    assert USAGE.startswith("Usage: /secrets")
    assert "check" in USAGE
    assert "never echoes" in PLAIN_EXPLANATION
    assert len(SECRET_PATTERNS) == len(SECRET_KINDS)
    assert [p.kind for p in SECRET_PATTERNS] == list(SECRET_KINDS)


def test_patterns_are_validated_data():
    for pattern in SECRET_PATTERNS:
        assert isinstance(pattern, SecretPattern)
        assert pattern.label
        assert pattern.basis in ("text", "filename")
    assert pattern_for_kind("secret_file").basis == "filename"
    assert pattern_for_kind("openai").kind == "openai_key"
    assert pattern_for_kind("env").kind == "env_assignment"
    assert validate_pattern(
        {"kind": "stripe", "label": "Stripe key"}) == SecretPattern(
            kind="stripe_key", label="Stripe key", basis="text")
    assert build_pattern(kind="github", label="GitHub token").kind \
        == "github_token"
    with pytest.raises(ValueError):
        validate_pattern({"kind": "stripe_key"})
    with pytest.raises(ValueError):
        validate_pattern({"kind": "stripe_key", "label": "x",
                          "surprise": 1})
    with pytest.raises(ValueError):
        pattern_for_kind("not_a_kind")


def test_kind_word_readings():
    assert normalize_secret_kind("openai_key") == "openai_key"
    assert normalize_secret_kind("OpenAI") == "openai_key"
    assert normalize_secret_kind("anthropic") == "anthropic_key"
    assert normalize_secret_kind("github-pat") == "github_token"
    assert normalize_secret_kind("AWS access") == "aws_access_key"
    assert normalize_secret_kind("aws_secret") == "aws_secret_key"
    assert normalize_secret_kind("STRIPE") == "stripe_key"
    assert normalize_secret_kind("slack") == "slack_token"
    assert normalize_secret_kind("google") == "google_api_key"
    assert normalize_secret_kind("xai") == "xai_key"
    assert normalize_secret_kind("bearer") == "bearer_token"
    assert normalize_secret_kind("url") == "url_credentials"
    assert normalize_secret_kind("private") == "private_key"
    assert normalize_secret_kind("generic") == "generic_secret"
    assert normalize_secret_kind("dotenv") == "env_assignment"
    assert normalize_secret_kind("filename") == "secret_file"
    with pytest.raises(ValueError):
        normalize_secret_kind("password_plaintext")
    with pytest.raises(ValueError):
        normalize_secret_kind("")
    with pytest.raises(ValueError):
        normalize_secret_kind(None)


def test_status_basis_and_id_readings():
    assert normalize_screening_status("clean") == "clean"
    assert normalize_screening_status("OK") == "clean"
    assert normalize_screening_status("blocked") == "refused"
    assert normalize_screening_status("Denied") == "refused"
    with pytest.raises(ValueError):
        normalize_screening_status("maybe")
    assert normalize_pattern_basis("text") == "text"
    assert normalize_pattern_basis("content") == "text"
    assert normalize_pattern_basis("name") == "filename"
    with pytest.raises(ValueError):
        normalize_pattern_basis("content-ish")
    assert normalize_hygiene_id("hygiene-1") == "hygiene-1"
    assert normalize_hygiene_id(" Hygiene-9.x ") == "Hygiene-9.x"
    with pytest.raises(ValueError):
        normalize_hygiene_id("two words")
    with pytest.raises(ValueError):
        normalize_hygiene_id("")


# -- finding kinds in text ---------------------------------------------


def test_secret_kinds_in_provider_shapes():
    assert secret_kinds_in(f"key: {FAKE_OPENAI}") == ("openai_key",)
    assert secret_kinds_in(FAKE_ANTHROPIC) == ("anthropic_key",)
    assert secret_kinds_in(FAKE_GITHUB) == ("github_token",)
    assert secret_kinds_in(FAKE_AWS_ACCESS) == ("aws_access_key",)
    assert secret_kinds_in(FAKE_STRIPE) == ("stripe_key",)
    assert secret_kinds_in(FAKE_SLACK) == ("slack_token",)
    assert secret_kinds_in(FAKE_GOOGLE) == ("google_api_key",)
    assert secret_kinds_in(FAKE_XAI) == ("xai_key",)
    assert secret_kinds_in(FAKE_PRIVATE_HEADER) == ("private_key",)


def test_secret_kinds_in_other_shapes():
    assert secret_kinds_in("Authorization: Bearer " + "FAKE9" * 6) \
        == ("bearer_token",)
    assert secret_kinds_in("https://user:FAKEpassw0rd@example.com/x") \
        == ("url_credentials",)
    assert "generic_secret" in secret_kinds_in(FAKE_GENERIC_LINE)
    env_line = "MY_SERVICE_TOKEN=FAKEVALUE123456"
    assert secret_kinds_in(env_line) == ("env_assignment",)
    assert secret_kinds_in("export APP_PASSWORD=FAKEVALUE123456") \
        == ("env_assignment",)


def test_secret_kinds_in_ordinary_text_and_refusals():
    assert secret_kinds_in("") == ()
    assert secret_kinds_in("just an ordinary sentence") == ()
    assert secret_kinds_in("the token bucket holds words") == ()
    assert secret_kinds_in("API_KEY=") == ()
    with pytest.raises(ValueError):
        secret_kinds_in(None)
    with pytest.raises(ValueError):
        secret_kinds_in(42)


def test_secret_kinds_in_kind_order():
    text = f"{FAKE_GITHUB} and {FAKE_OPENAI}"
    assert secret_kinds_in(text) == ("openai_key", "github_token")


# -- redaction ----------------------------------------------------------


def test_redaction_replaces_each_shape():
    cases = [
        FAKE_OPENAI, FAKE_ANTHROPIC, FAKE_GITHUB, FAKE_AWS_ACCESS,
        FAKE_STRIPE, FAKE_SLACK, FAKE_GOOGLE, FAKE_XAI,
        FAKE_PRIVATE_HEADER,
    ]
    for fake in cases:
        out = redact_secrets(f"before {fake} after")
        assert out == f"before {REDACTION_MARKER} after"
        assert fake not in out


def test_redaction_never_echoes_the_secret():
    text = f"a {FAKE_OPENAI} b {FAKE_GITHUB} c"
    out = redact_secrets(text)
    assert FAKE_OPENAI not in out
    assert FAKE_GITHUB not in out
    assert out.count(REDACTION_MARKER) == 2
    env = redact_secrets("MY_TOKEN=FAKEVALUE123456\nnext line")
    assert "FAKEVALUE123456" not in env
    assert env == f"MY_TOKEN={REDACTION_MARKER}\nnext line"
    generic = redact_secrets(FAKE_GENERIC_LINE)
    assert "FAKE8" not in generic


def test_redaction_leaves_ordinary_text_untouched():
    text = "an ordinary log line, nothing secret shaped here"
    assert redact_secrets(text) == text
    assert redact_secrets("") == ""
    assert redact_secrets(text, marker="***") == text


def test_redaction_marker_and_type_refusals():
    out = redact_secrets(f"x {FAKE_OPENAI}", marker="<hidden>")
    assert out == "x <hidden>"
    with pytest.raises(ValueError):
        redact_secrets(None)
    with pytest.raises(ValueError):
        redact_secrets(f"x {FAKE_OPENAI}", marker="  ")
    with pytest.raises(ValueError):
        redact_secrets(f"x {FAKE_OPENAI}", marker=None)


# -- filename screening ---------------------------------------------------


def test_filename_kinds_secret_names():
    assert filename_kinds(".env") == ("secret_file",)
    assert filename_kinds("config/.env.production") == ("secret_file",)
    assert filename_kinds("keys/id_rsa") == ("secret_file",)
    assert filename_kinds("keys/id_ed25519") == ("secret_file",)
    assert filename_kinds("certs/server.pem") == ("secret_file",)
    assert filename_kinds("certs/server.key") == ("secret_file",)
    assert filename_kinds("home/.ssh/config") == ("secret_file",)
    assert filename_kinds("docs/my_secret_notes.txt") == ("secret_file",)
    assert filename_kinds("credentials") == ("secret_file",)


def test_filename_kinds_ordinary_names():
    assert filename_kinds("src/main.py") == ()
    assert filename_kinds("README_AI.md") == ()
    assert filename_kinds("environment.py") == ()
    with pytest.raises(ValueError):
        filename_kinds("   ")
    with pytest.raises(ValueError):
        filename_kinds(None)


# -- the screening verdict ------------------------------------------------


def test_screen_file_clean_and_refused():
    clean = screen_file("src/main.py", "print('hello')\n")
    assert clean.status == "clean"
    assert clean.kinds == ()
    assert clean.refused is False
    refused = screen_file("src/config.py", f"KEY = '{FAKE_OPENAI}'\n")
    assert refused.status == "refused"
    assert refused.kinds == ("openai_key",)
    assert refused.refused is True
    by_name = screen_file(".env", "")
    assert by_name.status == "refused"
    assert by_name.kinds == ("secret_file",)
    both = screen_file("keys/server.pem", FAKE_GITHUB)
    assert both.kinds == ("github_token", "secret_file")


def test_screen_file_never_carries_content():
    secret = "FAKEVALUE123456"
    verdict = screen_file("app.py", f"MY_TOKEN={secret}\n")
    record = verdict.to_record()
    assert record["filename"] == "app.py"
    assert record["kinds"] == ["env_assignment"]
    assert secret not in repr(record)
    assert secret not in repr(verdict)
    assert secret not in verdict.display_label
    with pytest.raises(ValueError):
        screen_file("app.py", 42)
    with pytest.raises(ValueError):
        screen_file("", "text")


def test_screening_dataclass_validation():
    screening = FileScreening(filename="a.py", kinds=("openai",))
    assert screening.kinds == ("openai_key",)
    assert screening.status == "refused"
    assert Screening is FileScreening
    clean = FileScreening(filename="a.py")
    assert clean.status == "clean"
    with pytest.raises(ValueError):
        FileScreening(filename="a.py", kinds=("openai_key",),
                      status="clean")
    with pytest.raises(ValueError):
        FileScreening(filename="a.py", status="refused")
    with pytest.raises(ValueError):
        FileScreening(filename="a.py", kinds=("nope",))
    with pytest.raises(ValueError):
        FileScreening(filename="a.py", screening_id="two words")
    with pytest.raises(ValueError):
        FileScreening(filename=" ")


def test_build_and_validate_screening():
    built = build_screening({"file": "a.py", "kind": "github"})
    assert built.filename == "a.py"
    assert built.kinds == ("github_token",)
    assert built.status == "refused"
    words = build_screening(filename="b.py", status="clean")
    assert words.status == "clean"
    same = validate_screening(built)
    assert same is built
    with pytest.raises(ValueError):
        build_screening({"file": "a.py", "path": "other.py"})
    with pytest.raises(ValueError):
        build_screening({"kinds": ()})
    with pytest.raises(ValueError):
        build_screening({"filename": "a.py", "surprise": 1})
    with pytest.raises(ValueError):
        build_screening("a.py")


# -- the refusal record ---------------------------------------------------


def test_hygiene_record_only_for_refusals():
    assert hygiene_record(screen_file("a.py", "plain text")) is None
    refused = screen_file("keys/server.pem", FAKE_OPENAI)
    record = hygiene_record(refused)
    assert record["type"] == "secret_refusal"
    assert record["news"] is True
    assert record["slice"] == "M-110"
    assert record["filename"] == "keys/server.pem"
    assert record["kinds"] == ["openai_key", "secret_file"]
    assert "keys/server.pem" in record["headline"]
    assert FAKE_OPENAI not in repr(record)
    assert format_hygiene_record(record) == record["headline"]
    assert format_record(record) == record["headline"]
    with pytest.raises(ValueError):
        format_hygiene_record({"type": "something_else"})


# -- the registry ---------------------------------------------------------


def test_registry_deterministic_ids():
    registry = HygieneRegistry()
    first = registry.screen("a.py", "plain")
    second = registry.screen("b.py", FAKE_OPENAI)
    assert first.screening_id == "hygiene-1"
    assert second.screening_id == "hygiene-2"
    assert len(registry) == 2
    assert registry.get("hygiene-2") is second
    assert registry.list_screenings() == (first, second)
    named = registry.register(
        FileScreening(filename="c.py", screening_id="hygiene-9"))
    assert named.screening_id == "hygiene-9"
    third = registry.screen("d.py", "plain")
    assert third.screening_id == "hygiene-3"
    with pytest.raises(ValueError):
        registry.register(
            FileScreening(filename="e.py", screening_id="hygiene-9"))
    with pytest.raises(KeyError):
        registry.get("hygiene-404")


def test_registry_records():
    registry = _registry(
        FileScreening(filename="a.py"),
        FileScreening(filename=".env", kinds=("secret_file",)))
    assert registry.record("hygiene-1") is None
    record = registry.record("hygiene-2")
    assert record["type"] == "secret_refusal"
    assert record["filename"] == ".env"
    with pytest.raises(KeyError):
        registry.record("hygiene-404")


# -- formatters and the /secrets parser -----------------------------------


def test_format_pattern_and_patterns():
    line = format_pattern(pattern_for_kind("openai_key"))
    assert "openai_key" in line
    assert "text shape" in line
    whole = format_patterns()
    assert f"{len(SECRET_KINDS)} known" in whole
    assert "secret_file" in whole
    assert "filename shape" in whole


def test_format_screening_and_screenings():
    clean = format_screening(screen_file("a.py", "plain"))
    assert "clean" in clean
    assert "no secret pattern" in clean
    refused = format_screening(screen_file(".env", ""))
    assert "commit refused" in refused
    assert "secret file name" in refused
    assert "Content is never shown" in refused
    empty = format_screenings()
    assert "no files screened" in empty
    registry = _registry(screen_file("a.py", "plain"),
                         screen_file(".env", ""))
    whole = format_screenings(registry)
    assert "2 screened" in whole
    assert "hygiene-1" in whole
    assert "hygiene-2" in whole


def test_format_secrets_screen():
    screen = format_secrets_screen()
    assert "Secret hygiene (M-110)" in screen
    assert PLAIN_EXPLANATION in screen
    assert USAGE in screen
    assert "no files screened" in screen
    registry = _registry(screen_file(".env", ""))
    with_held = format_secrets_screen(registry)
    assert "1 screened" in with_held


def test_parse_secrets_args():
    assert parse_secrets_args("") == ("show", None)
    assert parse_secrets_args(None) == ("show", None)
    assert parse_secrets_args("show") == ("show", None)
    assert parse_secrets_args("status") == ("show", None)
    assert parse_secrets_args("show hygiene-1") == ("show", "hygiene-1")
    assert parse_secrets_args("hygiene-1") == ("show", "hygiene-1")
    assert parse_secrets_args("check .env") == ("check", ".env")
    assert parse_secrets_args("check src/app.py") == ("check", "src/app.py")
    for bad in ("check", "check a.py b.py", "show show", "status check",
                "openai_key", "show two words", "wipe hygiene-1"):
        with pytest.raises(ValueError):
            parse_secrets_args(bad)
    with pytest.raises(ValueError):
        parse_secrets_args(42)


# -- extra coverage -------------------------------------------------------


def test_each_provider_shape_redacts_individually():
    shapes = {
        "openai_key": FAKE_OPENAI, "anthropic_key": FAKE_ANTHROPIC,
        "github_token": FAKE_GITHUB, "aws_access_key": FAKE_AWS_ACCESS,
        "stripe_key": FAKE_STRIPE, "slack_token": FAKE_SLACK,
        "google_api_key": FAKE_GOOGLE, "xai_key": FAKE_XAI,
        "private_key": FAKE_PRIVATE_HEADER,
    }
    for kind, fake in shapes.items():
        assert secret_kinds_in(fake) == (kind,)
        assert fake not in redact_secrets(f"[{fake}]")


def test_bearer_and_url_shapes_redact():
    bearer = "Authorization: Bearer " + "FAKE9" * 6
    out = redact_secrets(bearer)
    assert "FAKE9" not in out
    url = "https://user:FAKEpassw0rd@example.com/x"
    out = redact_secrets(url)
    assert "FAKEpassw0rd" not in out


def test_aws_secret_assignment_shape():
    line = 'aws_secret = "' + "FAKEA" * 8 + '"'
    kinds = secret_kinds_in(line)
    assert "aws_secret_key" in kinds
    assert "FAKEA" not in redact_secrets(line)


def test_screening_kinds_deduplicated_and_ordered():
    verdict = screen_file("a.py", f"{FAKE_OPENAI} {FAKE_OPENAI} {FAKE_GITHUB}")
    assert verdict.kinds == ("openai_key", "github_token")
    built = build_screening(
        {"filename": "a.py", "kinds": ["github", "openai", "github"]})
    assert built.kinds == ("openai_key", "github_token")


def test_registry_screen_never_stores_content():
    registry = HygieneRegistry()
    secret = "FAKEVALUE123456"
    held = registry.screen("app.py", f"MY_TOKEN={secret}\n")
    assert secret not in repr(held)
    assert secret not in repr(registry.list_screenings())
    assert secret not in repr(registry.record(held.screening_id))


def test_pattern_build_refusals():
    with pytest.raises(ValueError):
        build_pattern({"kind": "stripe_key", "label": "x",
                       "basis": "sideways"})
    with pytest.raises(ValueError):
        build_pattern(42)
    pattern = build_pattern({"kind": "secret_file", "label": "s",
                             "basis": "name"})
    assert pattern.basis == "filename"


def test_format_screenings_from_list_source():
    listed = format_screenings([screen_file("a.py", "plain")])
    assert "1 screened" in listed
    single = format_screenings(screen_file(".env", ""))
    assert "1 screened" in single
    with pytest.raises(ValueError):
        format_screenings(42)


def test_parse_secrets_args_case_and_extra():
    assert parse_secrets_args("SHOW hygiene-2") == ("show", "hygiene-2")
    assert parse_secrets_args("Check .env") == ("check", ".env")
    with pytest.raises(ValueError):
        parse_secrets_args("check .env extra")
    with pytest.raises(ValueError):
        parse_secrets_args("secret_file")
