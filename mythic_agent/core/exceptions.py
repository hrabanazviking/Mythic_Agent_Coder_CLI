"""Unified exception taxonomy for Mythic Agent (roadmap slice R-008).

Every exception defined by ``mythic_agent`` derives from :class:`MythicError`,
so a single ``except MythicError`` catches all Mythic-internal failures while
letting unrelated ``ValueError`` / ``RuntimeError`` bugs from third-party code
propagate normally.

Each failure domain gets one category class carrying a machine-readable
``code`` attribute.  ``MythicError.to_dict()`` renders any exception as the
structured payload used by machine output::

    {"error": {"type": "ValidationError", "code": "validation_error",
               "message": "..."}}

This module imports nothing from the package (stdlib only), so any other
module can safely do ``from mythic_agent.core.exceptions import MythicError``
or ``from .exceptions import MythicValidationError`` without import cycles.

Migration table (slice R-008) -- class names are unchanged; only the bases
were widened.  Where a class already had a sensible builtin base, multiple
inheritance keeps the old ``except`` clauses working:

+----------------------------------+-----------------------------------------------+
| Class                            | New base(s) (decision)                        |
+==================================+===============================================+
| ``ValidationError``              | ``MythicValidationError, ValueError`` --      |
|                                  | schema/argument validation failures; ``except |
|                                  | ValueError`` still catches.                   |
+----------------------------------+-----------------------------------------------+
| ``SecurityError``                | ``MythicSecurityError, ValidationError`` --   |
|                                  | sandbox/policy violations are a kind of       |
|                                  | validation failure; ``except ValidationError``|
|                                  | and ``except ValueError`` still catch.        |
+----------------------------------+-----------------------------------------------+
| ``DependencyError``              | ``MythicExecutionError, ValueError`` --       |
| (agents/parallel)                | unknown ids / cycles surface while resolving  |
|                                  | parallel call graphs; ``except ValueError``   |
|                                  | still catches.                                |
+----------------------------------+-----------------------------------------------+
| ``ProviderCredentialsError``     | ``MythicProviderError, RuntimeError`` --      |
| (agents/llm)                     | missing LLM credential; ``except              |
|                                  | RuntimeError`` still catches.                 |
+----------------------------------+-----------------------------------------------+
| ``TurnCancelled`` (core/runtime) | ``MythicExecutionError, RuntimeError`` --     |
|                                  | cancellation is execution control flow;       |
|                                  | ``except RuntimeError`` still catches.        |
+----------------------------------+-----------------------------------------------+
| ``SessionBusy``                  | ``MythicSessionError, RuntimeError`` --       |
|                                  | another process owns the session; ``except    |
|                                  | RuntimeError`` still catches.                 |
+----------------------------------+-----------------------------------------------+
| ``SandboxError``                 | ``MythicSandboxError`` -- had no builtin      |
|                                  | base worth keeping; plain ``Exception`` added |
|                                  | nothing.                                      |
+----------------------------------+-----------------------------------------------+
| ``NotificationError``            | ``MythicNotificationError, RuntimeError`` --  |
|                                  | webhook/desktop delivery failure; ``except    |
|                                  | RuntimeError`` still catches.                 |
+----------------------------------+-----------------------------------------------+
| ``CheckpointError``              | ``MythicExecutionError`` -- missing/          |
| (workflow/slice_runner)          | unreadable slice checkpoint; had only plain   |
|                                  | ``Exception`` as a base.                      |
+----------------------------------+-----------------------------------------------+
| ``CorruptJournalLine``           | ``MythicJournalError`` -- checksum/parse      |
| (core/journal)                   | failure on a journal line; had only plain     |
|                                  | ``Exception`` as a base.                      |
+----------------------------------+-----------------------------------------------+
| ``ProviderError``                | ``MythicProviderError, RuntimeError`` --      |
| (providers/base)                 | any provider-side failure; ``except           |
|                                  | RuntimeError`` still catches.                 |
+----------------------------------+-----------------------------------------------+
| ``ProviderNotConfigured``,       | unchanged -- they already subclass            |
| ``ProviderNotFound``             | ``ProviderError`` and inherit the new         |
|                                  | taxonomy through it.                          |
+----------------------------------+-----------------------------------------------+
| ``GitHubCLIError``               | ``MythicIntegrationError, RuntimeError`` --   |
| (integrations/github)            | external ``gh`` CLI failure; ``except         |
|                                  | RuntimeError`` still catches.                 |
+----------------------------------+-----------------------------------------------+
| ``SnapshotError``                | ``MythicExecutionError`` -- unreadable/       |
| (core/repo_census)               | untrusted repo snapshot; had only plain       |
|                                  | ``Exception`` as a base.                      |
+----------------------------------+-----------------------------------------------+
"""


from __future__ import annotations

__all__ = [
    "Any",
    "CATEGORIES",
    "MythicConfigError",
    "MythicError",
    "MythicExecutionError",
    "MythicIntegrationError",
    "MythicJournalError",
    "MythicNotificationError",
    "MythicProviderError",
    "MythicSandboxError",
    "MythicSecurityError",
    "MythicSessionError",
    "MythicValidationError",
    "annotations",
]

from typing import Any


class MythicError(Exception):
    """Root of the Mythic Agent exception taxonomy.

    Catch this to handle every Mythic-internal failure with one clause.

    Attributes
    ----------
    code:
        Machine-readable snake_case category code.  Leaf classes inherit
        the code of their category unless they override it.
    """

    code = "mythic_error"

    def to_dict(self) -> dict[str, Any]:
        """Render this failure as structured machine output.

        Returns
        -------
        dict
            ``{"error": {"type": <class name>, "code": <code>,
            "message": <str(self)>}}``.
        """
        return {
            "error": {
                "type": type(self).__name__,
                "code": self.code,
                "message": str(self),
            }
        }


class MythicConfigError(MythicError):
    """Bad, missing, or unreadable configuration."""

    code = "config_error"


class MythicProviderError(MythicError):
    """LLM provider-side failure: auth, transport, malformed responses."""

    code = "provider_error"


class MythicValidationError(MythicError):
    """Input, argument, or schema validation failure."""

    code = "validation_error"


class MythicSecurityError(MythicError):
    """Security policy violation: sandbox escape, policy deny, path breach."""

    code = "security_error"


class MythicExecutionError(MythicError):
    """Failure during turn/call/slice execution, incl. cancellation."""

    code = "execution_error"


class MythicSessionError(MythicError):
    """Session ownership, locking, or lifecycle failure."""

    code = "session_error"


class MythicSandboxError(MythicError):
    """A command was refused by or could not run inside the sandbox."""

    code = "sandbox_error"


class MythicIntegrationError(MythicError):
    """External CLI/service integration failure (e.g. ``gh``)."""

    code = "integration_error"


class MythicJournalError(MythicError):
    """Write-ahead journal corruption or parse failure."""

    code = "journal_error"


class MythicNotificationError(MythicError):
    """Notification or webhook delivery failure."""

    code = "notification_error"


#: All taxonomy categories in declaration order.
CATEGORIES: tuple[type[MythicError], ...] = (
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
