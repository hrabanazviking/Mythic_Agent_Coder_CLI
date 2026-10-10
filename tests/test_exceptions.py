"""Exception taxonomy V2 tests (roadmap slice R-008).

Covers ``mythic_agent/core/exceptions.py`` and the migration of every
existing exception class onto the ``MythicError`` hierarchy:

* every known class is a ``MythicError`` subclass (table-driven);
* legacy ``except ValueError`` / ``except RuntimeError`` clauses still catch
  the classes that used those builtin bases (backward compatibility);
* ``to_dict()`` renders the documented machine-output shape;
* one raise+catch round-trip per taxonomy category;
* category ``code`` values are unique across the taxonomy.
"""

import pytest

from mythic_agent.core.exceptions import (
    CATEGORIES,
    MythicConfigError,
    MythicError,
    MythicExecutionError,
    MythicIntegrationError,
    MythicJournalError,
    MythicNotificationError,
    MythicProviderError,
    MythicSandboxError,
    MythicSecurityError,
    MythicSessionError,
    MythicValidationError,
)

from mythic_agent.agents.parallel import DependencyError
from mythic_agent.agents.llm import ProviderCredentialsError
from mythic_agent.core.runtime import TurnCancelled
from mythic_agent.core.validation import ValidationError, SecurityError
from mythic_agent.core.sessions import SessionBusy
from mythic_agent.core.sandbox import SandboxError
from mythic_agent.core.notifications import NotificationError
from mythic_agent.core.repo_census import SnapshotError
from mythic_agent.workflow.slice_runner import CheckpointError
from mythic_agent.core.journal import CorruptJournalLine
from mythic_agent.providers.base import (
    ProviderError,
    ProviderNotConfigured,
    ProviderNotFound,
)
from mythic_agent.integrations.github import GitHubCLIError


# (class, expected category)
TAXONOMY_TABLE = [
    (MythicConfigError, MythicConfigError),
    (DependencyError, MythicExecutionError),
    (ProviderCredentialsError, MythicProviderError),
    (TurnCancelled, MythicExecutionError),
    (ValidationError, MythicValidationError),
    (SecurityError, MythicSecurityError),
    (SessionBusy, MythicSessionError),
    (SandboxError, MythicSandboxError),
    (NotificationError, MythicNotificationError),
    (SnapshotError, MythicExecutionError),
    (CheckpointError, MythicExecutionError),
    (CorruptJournalLine, MythicJournalError),
    (ProviderError, MythicProviderError),
    (ProviderNotConfigured, MythicProviderError),
    (ProviderNotFound, MythicProviderError),
    (GitHubCLIError, MythicIntegrationError),
]


@pytest.mark.parametrize(
    "cls,category", TAXONOMY_TABLE, ids=[c.__name__ for c, _ in TAXONOMY_TABLE]
)
def test_every_known_class_is_mythic_error(cls, category):
    """Every migrated class derives from MythicError and its category."""
    assert issubclass(cls, MythicError)
    assert issubclass(cls, category)


@pytest.mark.parametrize("cls", [c for c, _ in TAXONOMY_TABLE])
def test_mythic_error_catches_everything(cls):
    """A single ``except MythicError`` handles all Mythic-internal failures."""
    try:
        raise cls("boom")
    except MythicError as exc:
        assert str(exc) == "boom"
    else:  # pragma: no cover - the raise above must not escape
        pytest.fail(f"{cls.__name__} escaped except MythicError")


@pytest.mark.parametrize(
    "cls", [ValidationError, SecurityError, DependencyError]
)
def test_legacy_value_error_catch_still_works(cls):
    """Backward compat: ``except ValueError`` still catches these classes."""
    try:
        raise cls("bad value")
    except ValueError:
        pass
    else:  # pragma: no cover
        pytest.fail(f"{cls.__name__} no longer caught by except ValueError")


@pytest.mark.parametrize(
    "cls",
    [
        ProviderCredentialsError,
        TurnCancelled,
        SessionBusy,
        NotificationError,
        ProviderError,
        ProviderNotConfigured,
        ProviderNotFound,
        GitHubCLIError,
    ],
)
def test_legacy_runtime_error_catch_still_works(cls):
    """Backward compat: ``except RuntimeError`` still catches these classes."""
    try:
        raise cls("runtime failure")
    except RuntimeError:
        pass
    else:  # pragma: no cover
        pytest.fail(f"{cls.__name__} no longer caught by except RuntimeError")


def test_security_error_still_validation_error():
    """SecurityError keeps its old ValidationError lineage too."""
    assert issubclass(SecurityError, ValidationError)
    try:
        raise SecurityError("denied")
    except ValidationError:
        pass
    else:  # pragma: no cover
        pytest.fail("SecurityError no longer caught by except ValidationError")


def test_provider_subclasses_inherit_taxonomy_through_provider_error():
    """ProviderNotConfigured/ProviderNotFound need no direct category base."""
    assert MythicProviderError in ProviderNotConfigured.__mro__
    assert MythicProviderError in ProviderNotFound.__mro__
    assert issubclass(ProviderNotConfigured, ProviderError)
    assert issubclass(ProviderNotFound, ProviderError)


def test_to_dict_shape():
    """to_dict() renders the documented machine-output payload."""
    exc = ValidationError("schema says no")
    assert exc.to_dict() == {
        "error": {
            "type": "ValidationError",
            "code": "validation_error",
            "message": "schema says no",
        }
    }


def test_to_dict_uses_most_derived_category_code():
    """A leaf class reports its own category's code, not an ancestor's."""
    assert SecurityError("denied").to_dict()["error"]["code"] == "security_error"
    assert ProviderNotFound("nope").to_dict()["error"]["code"] == "provider_error"
    assert TurnCancelled("stop").to_dict()["error"]["code"] == "execution_error"
    assert SandboxError("nope").to_dict()["error"]["code"] == "sandbox_error"
    assert CorruptJournalLine("bad line").to_dict()["error"]["code"] == "journal_error"
    assert MythicError("root").to_dict()["error"]["code"] == "mythic_error"


@pytest.mark.parametrize(
    "category,code",
    [
        (MythicConfigError, "config_error"),
        (MythicProviderError, "provider_error"),
        (MythicValidationError, "validation_error"),
        (MythicSecurityError, "security_error"),
        (MythicExecutionError, "execution_error"),
        (MythicSessionError, "session_error"),
        (MythicSandboxError, "sandbox_error"),
        (MythicIntegrationError, "integration_error"),
        (MythicJournalError, "journal_error"),
        (MythicNotificationError, "notification_error"),
    ],
    ids=[c.__name__ for c in CATEGORIES],
)
def test_raise_and_catch_one_instance_per_category(category, code):
    """One raise+catch round-trip per category, with the expected code."""
    assert category.code == code
    with pytest.raises(category) as record:
        raise category("category check")
    assert isinstance(record.value, MythicError)
    payload = record.value.to_dict()
    assert payload["error"]["type"] == category.__name__
    assert payload["error"]["code"] == code
    assert payload["error"]["message"] == "category check"


def test_codes_are_unique_across_taxonomy():
    """Machine codes must not collide between categories."""
    codes = [category.code for category in CATEGORIES]
    assert len(codes) == len(CATEGORIES) == 10
    assert len(set(codes)) == len(codes), f"duplicate codes: {codes}"
    assert "mythic_error" not in codes  # root keeps its own distinct code
    for code in codes:
        assert code.islower() and code.replace("_", "").isalnum()
        assert code.endswith("_error")


def test_categories_tuple_covers_ten_domains():
    """The public CATEGORIES tuple lists exactly the ten domains."""
    assert CATEGORIES == (
        MythicConfigError,
        MythicProviderError,
        MythicValidationError,
        MythicSecurityError,
        MythicExecutionError,
        MythicSessionError,
        MythicSandboxError,
        MythicIntegrationError,
        MythicJournalError,
        MythicNotificationError,
    )
    for category in CATEGORIES:
        assert issubclass(category, MythicError)
