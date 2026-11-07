"""Hook packs - the house hooks as installable packs (M-102).

Part V - Autonomy & Safety. The roadmap's words:
``the house hooks (run tests after edits, guard the
README, verify pushes) shipped as installable packs.``

What already shipped, and what this slice adds:

* M-101 ships the hooks lifecycle itself: the seven
  events as data, one hook (one event, one user script
  command) validated as data, a mechanical verdict for
  one finished run, and a block shaped as news. It
  ships no ready-made hooks - a user who wants the
  obvious house discipline (tests after edits, a guard
  on the README, a check before a push) must still
  write every hook mapping by hand.
* This slice is that missing shelf, as a pure layer:
  the house packs as validated data - each pack a
  named, described set of M-101 hooks, built and
  validated through the hooks module itself - a
  catalogue of the shipped packs with lookup by name,
  and install as pure data: a function that folds a
  pack's hooks into an existing hooks config list and
  returns the new hooks tuple. This module writes no
  file, changes no setting, runs no script and
  installs nothing in the world itself; the agent
  layer owns holding the configured hooks, storing an
  installed pack's hooks under the M-101 ``hooks``
  setting, and running them when their events fire.

Honesty rules, enforced here and pinned by tests:

* **Packs are hooks, nothing more.** Every hook in a
  pack is an M-101 ``Hook`` on a real event with a
  real command, validated through the hooks module -
  a pack can never smuggle in a hook the lifecycle
  itself would refuse.
* **The README guard never touches a README.** The
  guard pack's commands only read (``git diff``
  checks); no shipped pack carries a command that
  writes, edits or deletes any file, and the guard
  least of all the file it guards.
* **Malformed refuses.** An unknown key, an empty
  pack name or description, an empty hook command,
  duplicate hook or pack names and conflicting
  spellings of one field all raise instead of being
  skipped or guessed at; one bad entry refuses the
  whole list rather than silently narrowing what
  was written.
* **Install is explicit and idempotent.** Installing
  a pack adds exactly its missing hooks, in pack
  order, after the hooks already configured; a hook
  already present (same event, same command) is
  skipped, never duplicated, so installing the same
  pack twice changes nothing the second time. A
  pack hook whose *name* collides with a different
  configured hook refuses - a name is never silently
  rebound. The input list is never mutated; install
  returns a new tuple.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

from mythic_agent.core.hooks import Hook, validate_hook, validate_hooks

__all__ = [
    "HOOK_PACKS_SLICE",
    "PACK_NAMES",
    "PLAIN_EXPLANATION",
    "SHIPPED_PACKS",
    "USAGE",
    "Pack",
    "build_pack",
    "build_packs",
    "format_hook_packs",
    "format_pack",
    "format_packs",
    "format_packs_status",
    "get_pack",
    "hooks_for_pack",
    "install_pack",
    "normalize_pack_name",
    "pack_label",
    "resolve_pack",
    "shipped_packs",
    "validate_pack",
    "validate_packs",
]

HOOK_PACKS_SLICE = "M-102"

PLAIN_EXPLANATION = (
    "Hook packs are the house hooks shipped as "
    "installable packs: each pack is a named, "
    "described set of hooks from the hooks lifecycle "
    "(M-101), validated through that layer. The "
    "shipped shelf holds three packs - "
    "tests_after_edits runs the test suite after "
    "edits, readme_guard guards the README with "
    "read-only checks, and verify_pushes verifies "
    "the work at commit time before it can be "
    "pushed. Installing a pack folds its hooks into "
    "the configured hooks as pure data: it is "
    "explicit, idempotent, and never mutates the "
    "list it is given. This layer validates and "
    "formats only; it runs no script itself."
)

USAGE = (
    "Usage: /hookpacks, /hookpacks list, "
    "/hookpacks show, /hookpacks show <pack>, "
    "/hookpacks install <pack>"
)

_PACK_KEYS = frozenset(
    {"name", "title", "description", "summary", "hooks"})


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def normalize_pack_name(value: Any) -> str:
    """The canonical pack name a word names, or a refusal.

    Pack names read case-insensitively, with dashes
    read as underscores (``readme-guard`` is
    ``readme_guard``) - the same reading the hooks
    layer gives its event words. A name that is not
    a non-empty run of letters, digits and
    underscores once read that way raises.
    """
    if isinstance(value, str):
        wanted = value.strip().lower().replace("-", "_")
        if wanted and all(
                ch.isalnum() or ch == "_" for ch in wanted):
            return wanted
    raise ValueError(f"a pack name must be a non-empty name, got {value!r}")


def _check_pack_hooks(hooks: Any) -> Tuple[Hook, ...]:
    """A pack's hooks, validated whole, as a tuple.

    A pack needs at least one hook; every entry must
    already be an M-101 ``Hook`` (mapping data goes
    through :func:`validate_pack`, which builds them
    first). Two hooks sharing one name, or one event
    and command, refuse - a pack never carries the
    same hook twice under two spellings.
    """
    if isinstance(hooks, (str, bytes)) or not isinstance(
            hooks, (list, tuple)):
        raise ValueError("a pack's hooks must be a list of hooks")
    checked = tuple(hooks)
    if not checked:
        raise ValueError("a pack needs at least one hook")
    for hook in checked:
        if not isinstance(hook, Hook):
            raise ValueError(
                f"a pack's hooks must be hooks, got {hook!r}")
    seen_names = set()
    seen_pairs = set()
    for hook in checked:
        if hook.name:
            key = hook.name.lower()
            if key in seen_names:
                raise ValueError(
                    f"a pack names two hooks {hook.name!r}")
            seen_names.add(key)
        pair = (hook.event, hook.command)
        if pair in seen_pairs:
            raise ValueError(
                "a pack carries the same hook twice: "
                f"{hook.event} {hook.command!r}")
        seen_pairs.add(pair)
    return checked


# ---------------------------------------------------------------------
# The pack: one named, described set of hooks, as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Pack:
    """One hook pack: a name, a description, its hooks.

    Constructing one validates it - a malformed name,
    a blank description, no hooks, a non-hook entry,
    duplicate hook names and a hook carried twice all
    raise - so a Pack that exists is a pack the agent
    layer could install.
    """

    name: str
    description: str
    hooks: Tuple[Hook, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "name", normalize_pack_name(self.name))
        object.__setattr__(
            self, "description",
            _clean_text(self.description, "a pack description"))
        object.__setattr__(self, "hooks", _check_pack_hooks(self.hooks))

    @property
    def label(self) -> str:
        """The pack's canonical name."""
        return self.name

    @property
    def hook_count(self) -> int:
        return len(self.hooks)

    @property
    def events(self) -> Tuple[str, ...]:
        """The events this pack's hooks ride, in pack order."""
        seen = []
        for hook in self.hooks:
            if hook.event not in seen:
                seen.append(hook.event)
        return tuple(seen)

    def to_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "hooks": [hook.to_record() for hook in self.hooks],
        }


def pack_label(pack: Any) -> str:
    """The canonical name one pack is reported under."""
    if isinstance(pack, Pack):
        return pack.name
    return normalize_pack_name(pack)


def validate_pack(spec: Any) -> Pack:
    """Validate one pack mapping into a Pack.

    The mapping names a ``name`` (or ``title``), a
    ``description`` (or ``summary``) and a non-empty
    ``hooks`` list of hook mappings (or Hooks), each
    validated through the M-101 hooks layer. Naming
    both spellings of one field with different values
    refuses, and unknown keys refuse - a pack is never
    repaired by guessing.
    """
    if isinstance(spec, Pack):
        return spec
    if not isinstance(spec, dict):
        raise ValueError("a hook pack must be a mapping")
    unknown = set(spec) - _PACK_KEYS
    if unknown:
        raise ValueError(
            "unknown hook pack keys: %s" % ", ".join(sorted(unknown)))
    name = spec.get("name", spec.get("title"))
    if name is None:
        raise ValueError("a hook pack is missing its name")
    if "name" in spec and "title" in spec \
            and spec["name"] != spec["title"]:
        raise ValueError("a hook pack names two different names")
    description = spec.get("description", spec.get("summary"))
    if description is None:
        raise ValueError("a hook pack is missing its description")
    if "description" in spec and "summary" in spec \
            and spec["description"] != spec["summary"]:
        raise ValueError("a hook pack names two different descriptions")
    if "hooks" not in spec:
        raise ValueError("a hook pack is missing its hooks")
    raw_hooks = spec["hooks"]
    if isinstance(raw_hooks, (str, bytes)) or not isinstance(
            raw_hooks, (list, tuple)):
        raise ValueError("a hook pack's hooks must be a list of hooks")
    hooks = tuple(
        hook if isinstance(hook, Hook) else validate_hook(hook)
        for hook in raw_hooks)
    return Pack(name=name, description=description, hooks=hooks)


def build_pack(name: Any, description: Any,
               hooks: Sequence[Any]) -> Pack:
    """Build one validated pack from its pieces."""
    if isinstance(hooks, (str, bytes)) or not isinstance(
            hooks, (list, tuple)):
        raise ValueError("a hook pack's hooks must be a list of hooks")
    built = tuple(
        hook if isinstance(hook, Hook) else validate_hook(hook)
        for hook in hooks)
    return Pack(name=name, description=description, hooks=built)


def validate_packs(specs: Any) -> Tuple[Pack, ...]:
    """Validate a whole pack list, in listed order.

    ``None`` is the empty list. Every pack must
    validate, and two packs sharing one canonical
    name refuse - one bad or duplicated entry refuses
    the whole list rather than silently narrowing
    what was written.
    """
    if specs is None:
        return ()
    if isinstance(specs, (str, bytes)) or not isinstance(
            specs, (list, tuple)):
        raise ValueError("hook packs must be a list of packs")
    packs = tuple(validate_pack(spec) for spec in specs)
    seen = set()
    for pack in packs:
        if pack.name in seen:
            raise ValueError(f"two hook packs named {pack.name!r}")
        seen.add(pack.name)
    return packs


#: The list builder under its building name.
build_packs = validate_packs


# ---------------------------------------------------------------------
# The shipped catalogue: the house packs, as validated data.
# ---------------------------------------------------------------------


#: The shipped house packs, in shelf order. Every hook
#: is built here through the same validation a user
#: mapping goes through, so the shelf can never drift
#: from what the hooks layer itself would accept.
SHIPPED_PACKS: Tuple[Pack, ...] = validate_packs([
    {
        "name": "tests_after_edits",
        "description": (
            "Run the test suite after edits, so a broken "
            "edit is caught the moment it lands."),
        "hooks": [
            {"event": "post_edit", "command": "python -m pytest -q",
             "name": "run-tests-after-edit", "timeout_seconds": 300},
            {"event": "post_edit",
             "command": "python -m compileall -q mythic_agent",
             "name": "compile-after-edit", "timeout_seconds": 120},
        ],
    },
    {
        "name": "readme_guard",
        "description": (
            "Guard the README: refuse an edit-time or "
            "commit-time state where the README has "
            "changed, using read-only checks only - this "
            "pack never modifies a README itself."),
        "hooks": [
            {"event": "on_commit",
             "command": "git diff --cached --quiet -- README.md",
             "name": "readme-guard-commit"},
            {"event": "pre_edit",
             "command": "git diff --quiet -- README.md",
             "name": "readme-guard-edit"},
        ],
    },
    {
        "name": "verify_pushes",
        "description": (
            "Verify the work at commit time - the suite "
            "green and the diff clean - before it can "
            "be pushed."),
        "hooks": [
            {"event": "on_commit", "command": "python -m pytest -q",
             "name": "verify-tests-before-push",
             "timeout_seconds": 300},
            {"event": "on_commit", "command": "git diff --check",
             "name": "verify-clean-diff"},
        ],
    },
])

#: The shipped pack names, in shelf order.
PACK_NAMES: Tuple[str, ...] = tuple(pack.name for pack in SHIPPED_PACKS)


def shipped_packs() -> Tuple[Pack, ...]:
    """The shipped catalogue, in shelf order."""
    return SHIPPED_PACKS


def get_pack(name: Any) -> Pack:
    """The shipped pack *name* names, or a refusal.

    The name reads case-insensitively, with dashes
    read as underscores, exactly as pack names are
    canonicalised. An unknown name raises - a pack
    this layer does not ship is never guessed at.
    """
    wanted = normalize_pack_name(name)
    for pack in SHIPPED_PACKS:
        if pack.name == wanted:
            return pack
    raise ValueError(
        "a hook pack must be one of %s, got %r"
        % ("/".join(PACK_NAMES), name))


def resolve_pack(pack: Any) -> Pack:
    """The Pack *pack* names: a Pack, a shipped name, or a mapping."""
    if isinstance(pack, Pack):
        return pack
    if isinstance(pack, str):
        return get_pack(pack)
    if isinstance(pack, dict):
        return validate_pack(pack)
    raise ValueError(f"a hook pack needs a pack or its name, got {pack!r}")


def hooks_for_pack(pack: Any) -> Tuple[Hook, ...]:
    """The hooks one pack carries, in pack order."""
    return resolve_pack(pack).hooks


# ---------------------------------------------------------------------
# Install, as pure data.
# ---------------------------------------------------------------------


def install_pack(hooks: Any, pack: Any) -> Tuple[Hook, ...]:
    """Install *pack* into *hooks*, as a new hooks tuple.

    Install is explicit and idempotent. The existing
    hooks are validated whole through the M-101 layer
    (``None`` is the empty list; one malformed hook
    refuses the install) and keep their order; the
    pack's hooks follow in pack order. A pack hook
    whose event and command already appear among the
    existing hooks is skipped, never duplicated - so
    installing the same pack twice returns the same
    tuple the second time. A pack hook whose *name*
    (read case-insensitively) already names a
    different configured hook refuses the whole
    install rather than silently rebinding the name.
    The input is never mutated.
    """
    existing = validate_hooks(hooks)
    resolved = resolve_pack(pack)
    present_pairs = {(hook.event, hook.command) for hook in existing}
    by_name = {
        hook.name.lower(): hook for hook in existing if hook.name}
    merged = list(existing)
    for hook in resolved.hooks:
        if (hook.event, hook.command) in present_pairs:
            continue
        if hook.name and hook.name.lower() in by_name:
            raise ValueError(
                f"a hook named {hook.name!r} is already configured "
                "with a different event or command")
        merged.append(hook)
        present_pairs.add((hook.event, hook.command))
        if hook.name:
            by_name[hook.name.lower()] = hook
    return tuple(merged)


# ---------------------------------------------------------------------
# The /hookpacks surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_pack(pack: Any) -> str:
    """One pack, in plain words, from the pack."""
    validated = resolve_pack(pack)
    events = ", ".join(validated.events)
    return (
        f"{validated.name}: {validated.description} "
        f"({validated.hook_count} hook(s) on {events})")


def format_packs(packs: Any = None) -> str:
    """The packs, in plain words, in order.

    With no argument the shipped catalogue is listed.
    With no packs at all the text starts with the
    plain statement of that fact.
    """
    selected = SHIPPED_PACKS if packs is None else validate_packs(packs)
    if not selected:
        return (
            "Hook packs: none shipped. No house hooks "
            "are available to install.")
    lines = [f"Hook packs: {len(selected)} shipped."]
    for pack in selected:
        lines.append(f"  {format_pack(pack)}")
    return "\n".join(lines)


def format_packs_status(packs: Any = None) -> str:
    """The one-line status of the pack shelf."""
    selected = SHIPPED_PACKS if packs is None else validate_packs(packs)
    if not selected:
        return "Hook packs: none shipped."
    names = ", ".join(pack.name for pack in selected)
    hooks = sum(pack.hook_count for pack in selected)
    return f"Hook packs: {len(selected)} shipped ({names}); {hooks} hook(s)."


def format_hook_packs(packs: Any = None) -> str:
    """The whole slice, in plain words, for /hookpacks."""
    lines = ["Hook packs (M-102) - " + PLAIN_EXPLANATION, ""]
    lines.append(format_packs(packs))
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


def parse_hook_packs_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /hookpacks grammar both surfaces share.

    No words (or ``list`` / ``show``) shows the shelf;
    ``show <pack>`` and a bare pack name show one pack;
    ``install <pack>`` installs one pack. The pack
    name is validated and canonicalised here, against
    the shipped catalogue. Anything else is a usage
    error naming the grammar.
    Returns ``(action, pack-name-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() in ("list", "show"):
        return ("show", None)
    words = text.split()
    head = words[0].lower()
    if head in ("show", "install") and len(words) == 2:
        try:
            return (head, get_pack(words[1]).name)
        except ValueError:
            raise ValueError(USAGE) from None
    if len(words) == 1:
        try:
            return ("show", get_pack(words[0]).name)
        except ValueError:
            raise ValueError(USAGE) from None
    raise ValueError(USAGE)
