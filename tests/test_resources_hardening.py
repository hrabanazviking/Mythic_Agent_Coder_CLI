"""R-010: resource/data loading hardening.

Covers the hardened contracts in ``mythic_agent.resources`` and
``mythic_agent.data.data_loader``:

* missing resource file -> ``FileNotFoundError`` naming the expected path
* malformed YAML (strict) -> ``ValidationError`` with file path + line/column
* oversized files (>1 MiB) rejected before parsing; just under the limit loads
* path traversal (``..``, absolute paths) rejected
* empty file -> empty mapping (documented), not a crash
* existing fallback behavior (non-strict) is preserved for valid inputs
"""

import pytest

from mythic_agent.core.validation import SecurityError, ValidationError
from mythic_agent.data.data_loader import (
    MAX_RESOURCE_BYTES,
    RobustDataLoader,
    data_loader,
)
from mythic_agent.resources import (
    load_resource,
    resource_path,
    resource_root,
)

BROKEN_YAML = "top: ok\n  bad: indent\n"  # mapping values not allowed, line 2


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --- missing files --------------------------------------------------------


def test_missing_resource_error_names_expected_path():
    with pytest.raises(FileNotFoundError) as excinfo:
        load_resource("definitely_not_a_resource.yaml")
    message = str(excinfo.value)
    assert "definitely_not_a_resource.yaml" in message
    assert str(resource_root()) in message


def test_strict_loader_missing_file_names_expected_path(tmp_path):
    missing = tmp_path / "gone.yaml"
    with pytest.raises(FileNotFoundError) as excinfo:
        RobustDataLoader.load_yaml(missing, strict=True)
    assert str(missing) in str(excinfo.value)
    with pytest.raises(FileNotFoundError):
        RobustDataLoader.load_json(tmp_path / "gone.json", strict=True)
    with pytest.raises(FileNotFoundError):
        RobustDataLoader.load_markdown(tmp_path / "gone.md", strict=True)


# --- malformed YAML --------------------------------------------------------


def test_malformed_yaml_raises_validation_error_with_line_info(tmp_path):
    path = _write(tmp_path, "broken.yaml", BROKEN_YAML)
    with pytest.raises(ValidationError) as excinfo:
        RobustDataLoader.load_yaml(path, strict=True)
    message = str(excinfo.value)
    assert str(path) in message
    assert "line 2" in message
    assert "column" in message


def test_malformed_yaml_via_singleton_and_read_any(tmp_path):
    path = _write(tmp_path, "broken.yml", BROKEN_YAML)
    with pytest.raises(ValidationError):
        data_loader.load_yaml(path, strict=True)
    with pytest.raises(ValidationError):
        RobustDataLoader.read_any(path, strict=True)


# --- size limits -----------------------------------------------------------


def _yaml_payload_of_size(total_bytes):
    # "key: " + "v" * n + "\n" == n + 6 bytes, valid YAML mapping.
    n = total_bytes - 6
    assert n > 0
    return "key: " + "v" * n + "\n"


def test_oversize_yaml_rejected_before_parsing(tmp_path):
    path = _write(tmp_path, "big.yaml", _yaml_payload_of_size(MAX_RESOURCE_BYTES + 1))
    assert path.stat().st_size == MAX_RESOURCE_BYTES + 1
    with pytest.raises(ValidationError) as excinfo:
        RobustDataLoader.load_yaml(path, strict=True)
    message = str(excinfo.value)
    assert str(path) in message
    assert str(MAX_RESOURCE_BYTES) in message
    # The non-strict soft contract also refuses to feed oversized input to a parser.
    with pytest.raises(ValidationError):
        RobustDataLoader.load_yaml(path)
    with pytest.raises(ValidationError):
        RobustDataLoader.read_any(path, strict=True)


def test_just_under_limit_yaml_accepted(tmp_path):
    path = _write(tmp_path, "almost.yaml", _yaml_payload_of_size(MAX_RESOURCE_BYTES - 1))
    assert path.stat().st_size == MAX_RESOURCE_BYTES - 1
    parsed = RobustDataLoader.load_yaml(path, strict=True)
    assert isinstance(parsed, dict) and parsed["key"].startswith("vvv")


def test_oversize_json_rejected_before_parsing(tmp_path):
    payload = '{"key": "' + "v" * (MAX_RESOURCE_BYTES) + '"}'
    path = _write(tmp_path, "big.json", payload)
    assert path.stat().st_size > MAX_RESOURCE_BYTES
    with pytest.raises(ValidationError):
        RobustDataLoader.load_json(path, strict=True)


def test_size_limit_is_one_mib():
    assert MAX_RESOURCE_BYTES == 1024 * 1024


# --- path traversal --------------------------------------------------------


@pytest.mark.parametrize("evil", ["../evil", "../../evil", "a/../../evil", "/abs/path"])
def test_traversal_names_rejected(evil):
    with pytest.raises(ValidationError):
        resource_path(evil)
    with pytest.raises(ValidationError):
        load_resource(evil)


def test_traversal_rejection_is_security_error():
    with pytest.raises(SecurityError):
        resource_path("../evil")


def test_null_byte_name_rejected():
    with pytest.raises(ValidationError):
        resource_path("evil\x00.yaml")


def test_dotdot_rejected_even_when_it_would_stay_inside():
    # Defense in depth: any ".." segment is rejected, not just escaping ones.
    with pytest.raises(ValidationError):
        resource_path("subdir/../runtime_defaults.yaml")


def test_plain_relative_name_resolves_inside_root():
    resolved = resource_path("runtime_defaults.yaml")
    assert resolved == resource_root().resolve() / "runtime_defaults.yaml"


# --- empty files -----------------------------------------------------------


def test_empty_yaml_is_empty_mapping_in_strict_mode(tmp_path):
    path = _write(tmp_path, "empty.yaml", "")
    assert RobustDataLoader.load_yaml(path, strict=True) == {}


def test_empty_json_is_empty_mapping_in_strict_mode(tmp_path):
    path = _write(tmp_path, "empty.json", "")
    assert RobustDataLoader.load_json(path, strict=True) == {}


def test_comments_only_yaml_is_empty_mapping_in_strict_mode(tmp_path):
    path = _write(tmp_path, "comments.yaml", "# nothing here\n# just comments\n")
    assert RobustDataLoader.load_yaml(path, strict=True) == {}


# --- regression: valid loads and legacy fallback behavior ------------------


def test_load_resource_valid_yaml_regression():
    data = load_resource("runtime_defaults.yaml")
    assert isinstance(data, dict)
    assert data["request_timeout"] == 120.0
    assert data["max_retries"] == 2


def test_load_resource_all_shipped_data_files():
    for name in ("config_defaults.yaml", "permissions.yaml", "runtime_defaults.yaml"):
        assert isinstance(load_resource(name), dict)


def test_load_resource_format_override():
    data = load_resource("runtime_defaults.yaml", format="yaml")
    assert isinstance(data, dict) and "request_timeout" in data


def test_valid_json_and_markdown_still_load(tmp_path):
    as_json = _write(tmp_path, "ok.json", '{"a": 1}')
    assert RobustDataLoader.load_json(as_json, strict=True) == {"a": 1}
    as_md = _write(tmp_path, "ok.md", "# hi\n")
    assert RobustDataLoader.load_markdown(as_md, strict=True) == "# hi\n"
    assert RobustDataLoader.read_any(as_json, strict=True) == {"a": 1}


def test_non_strict_fallback_behavior_preserved(tmp_path):
    missing = tmp_path / "missing.yaml"
    assert RobustDataLoader.load_yaml(missing) is None
    assert RobustDataLoader.load_yaml(missing, fallback="fb") == "fb"
    assert RobustDataLoader.load_json(tmp_path / "missing.json", fallback=[]) == []
    assert RobustDataLoader.load_markdown(tmp_path / "missing.md") == ""
    # Malformed YAML in soft mode still yields the fallback, not an exception.
    broken = _write(tmp_path, "broken.yaml", BROKEN_YAML)
    assert RobustDataLoader.load_yaml(broken, fallback="fb") == "fb"
    # Empty file in soft mode still yields None (legacy contract: safe_load("") is None).
    empty = _write(tmp_path, "empty.yaml", "")
    assert RobustDataLoader.load_yaml(empty, fallback="fb") is None
    # Strict-mode JSON syntax errors surface the parser error with line info.
    bad_json = _write(tmp_path, "bad.json", '{"a": }')
    with pytest.raises(Exception) as excinfo:
        RobustDataLoader.load_json(bad_json, strict=True)
    assert "line 1" in str(excinfo.value)
