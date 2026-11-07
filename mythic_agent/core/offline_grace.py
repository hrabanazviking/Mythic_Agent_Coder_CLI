"""Offline and degraded grace (All-Features roadmap slice M-115).

Part V - Autonomy & Safety. The roadmap words:
``provider down, LSP down, net down - each failure
narrows the coder honestly and says what it lost.``

What already shipped, and what this slice adds:

* The provider health board (``provider_health.py``,
  M-039) reports each provider door by door:
  ``reachable`` / ``unreachable`` / ``needs-key`` /
  ``unknown``. Nothing turned a failure like that
  into a plain statement of what the coder lost.
* Offline honesty (``offline_honesty.py``, M-040)
  declares the whole offline state from a probed
  board, once, and names the non-model tools that
  still work. Nothing held a PARTIAL failure - a
  dead language server beside a live provider, a
  dead network beside a live local model - as data.
* The LSP clients (M-049 diagnostics, M-050
  navigation, M-051 rename and code actions) give
  the coder language-server sight. Nothing said,
  in plain words, what is lost when that sight goes.
* This slice is that missing degraded layer, as a
  pure layer in the exact sibling shape: failure
  kinds held as validated data with the capability
  each one loses stated honestly in plain words, a
  mechanical judge that derives the current
  degradation state from given evidence only, a
  degradation record shaped as session news, and a
  small in-memory registry model with deterministic
  ids. This module probes nothing, opens no
  connection, writes no file, changes no setting
  and imports no agent / UI code; the agent layer
  owns gathering evidence and holding the registry
  for a session.

Honesty rules, enforced here and pinned by tests:

* **State is derived, never invented.** The judge
  reads only the evidence it is given, dimension
  by dimension. A dimension whose evidence is
  ``unknown`` is never read as up and never read
  as down: it is named unknown in the reasons.
* **Full is claimed only from full evidence.**
  The state is ``full`` only when every dimension
  affirmatively answers (provider reachable, LSP
  up, network up). Any unknown dimension with no
  known failure leaves the state ``unknown``.
* **Each failure says what it lost.** Every known
  failure names, in plain words, the capabilities
  it narrows away and the work that still stands.
  A failure is never stated as a bare colour,
  symbol or code.
* **One failure never invents another.** A dead
  network does not by itself declare a local
  provider down, and a dead provider does not by
  itself declare the language server down. Only
  the evidence given is judged.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "FAILURE_KINDS",
    "FAILURE_PHRASES",
    "KEPT_CAPABILITIES",
    "LOST_CAPABILITIES",
    "OFFLINE_GRACE_SLICE",
    "PLAIN_EXPLANATION",
    "STATES",
    "USAGE",
    "Assessment",
    "DegradationAssessment",
    "DegradationFailure",
    "DegradationRegistry",
    "Failure",
    "Registry",
    "build_failure",
    "format_assessment",
    "format_failure",
    "format_failures",
    "format_grace_record",
    "format_grace_screen",
    "format_record",
    "judge_degradation",
    "normalize_failure_kind",
    "normalize_lsp_status",
    "normalize_network_status",
    "normalize_provider_status",
    "normalize_record_id",
    "parse_grace_args",
    "plain_words",
    "degradation_record",
    "validate_failure",
]

OFFLINE_GRACE_SLICE = "M-115"

#: The failure kinds this layer speaks of, in
#: roadmap order: the provider, the language
#: server, the network.
FAILURE_KINDS = ("provider_down", "lsp_down", "network_down")

#: Each failure kind, said in plain words.
FAILURE_PHRASES = {
    "provider_down": "the model provider is down",
    "lsp_down": "the language server (LSP) is down",
    "network_down": "the network is down",
}

_KIND_WORDS = {
    "provider_down": "provider_down",
    "provider-down": "provider_down",
    "provider down": "provider_down",
    "provider": "provider_down",
    "provider_unreachable": "provider_down",
    "unreachable": "provider_down",
    "lsp_down": "lsp_down",
    "lsp-down": "lsp_down",
    "lsp down": "lsp_down",
    "lsp": "lsp_down",
    "language_server_down": "lsp_down",
    "network_down": "network_down",
    "network-down": "network_down",
    "network down": "network_down",
    "network": "network_down",
    "net_down": "network_down",
    "net down": "network_down",
    "offline": "network_down",
}

#: What each failure takes away, in plain words.
LOST_CAPABILITIES = {
    "provider_down": (
        "model answers - no provider door is serving, "
        "so the coder cannot ask a model to write, "
        "explain or judge code",
    ),
    "lsp_down": (
        "language-server diagnostics - errors and "
        "warnings from the language server no longer "
        "flow into the coder awareness",
        "language-server navigation - go-to-definition, "
        "references, hover and workspace symbols no "
        "longer answer",
        "language-server rename and code actions - a "
        "rename no longer propagates by the server "
        "own knowledge",
    ),
    "network_down": (
        "every remote provider door - a provider "
        "reached over the network cannot serve",
        "remote and SSH work against another machine",
        "any fetch from the network",
    ),
}

#: What still stands under each failure, in plain words.
KEPT_CAPABILITIES = {
    "provider_down": (
        "the non-model tools still work: static review, "
        "recorded metrics and session search",
        "local file reading and editing still work",
    ),
    "lsp_down": (
        "text and structural search still work",
        "local file reading and editing still work",
        "the model provider still answers, if it is up",
    ),
    "network_down": (
        "a local model still answers, if one is running",
        "local file reading and editing still work",
        "the non-model tools still work: static review, "
        "recorded metrics and session search",
    ),
}

#: The degradation states, in honesty order.
STATES = ("full", "degraded", "unknown")

PLAIN_EXPLANATION = (
    "Offline and degraded grace: when part of the "
    "coder world fails - the model provider down, "
    "the language server (LSP) down, the network "
    "down - the coder narrows honestly and says "
    "what it lost, in plain words, and what still "
    "stands. The state is judged only from evidence "
    "given: full is claimed only when the provider, "
    "the language server and the network all "
    "affirmatively answer; a dimension whose "
    "evidence is unknown is named unknown, never "
    "guessed up or down; and one failure never "
    "invents another. This layer holds degradation "
    "as data only; the agent layer gathers the "
    "evidence and announces a change."
)

USAGE = (
    "Usage: /grace, /grace show, "
    "/grace show <record>, /grace failures"
)

_ID_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789-_.")


def _clean_text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a non-empty string")
    return value.strip()


def _pick(mapping: Dict[str, Any], names: Tuple[str, ...],
          what: str) -> Any:
    found = [name for name in names if name in mapping]
    if not found:
        return None
    first = mapping[found[0]]
    for name in found[1:]:
        if mapping[name] != first:
            raise ValueError(
                f"degradation evidence names two different {what}")
    return first


def normalize_failure_kind(value: Any) -> str:
    """The canonical failure kind a word names.

    Reads the three roadmap kinds and their plain
    spellings, case-insensitively. Any other word
    refuses: the failure vocabulary is closed, so
    a failure this layer does not speak of is never
    guessed into one it does.
    """
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in _KIND_WORDS:
            return _KIND_WORDS[wanted]
        underscored = wanted.replace("-", "_").replace(" ", "_")
        for key, kind in _KIND_WORDS.items():
            if key.replace("-", "_").replace(" ", "_") == underscored:
                return kind
    raise ValueError(
        "a failure kind must be one of %s, got %r"
        % ("/".join(FAILURE_KINDS), value))


def normalize_provider_status(value: Any) -> str:
    """One provider dimension answer, in M-039 board words.

    The board statuses are the vocabulary:
    ``reachable`` / ``unreachable`` / ``needs-key``
    / ``unknown``. A missing answer (None) is
    ``unknown`` - never reachable, never down.
    Any other word refuses.
    """
    if value is None:
        return "unknown"
    if isinstance(value, str):
        wanted = value.strip().lower().replace("_", "-")
        if wanted in ("reachable", "up", "ok"):
            return "reachable"
        if wanted in ("unreachable", "down"):
            return "unreachable"
        if wanted == "needs-key":
            return "needs-key"
        if wanted == "unknown":
            return "unknown"
    raise ValueError(
        f"a provider status must be reachable, unreachable, "
        f"needs-key or unknown, got {value!r}")


def normalize_lsp_status(value: Any) -> str:
    """One language-server dimension answer: up, down or unknown."""
    if value is None:
        return "unknown"
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in ("up", "running", "available", "reachable"):
            return "up"
        if wanted in ("down", "stopped", "unreachable", "dead"):
            return "down"
        if wanted == "unknown":
            return "unknown"
    raise ValueError(
        f"an LSP status must be up, down or unknown, got {value!r}")


def normalize_network_status(value: Any) -> str:
    """One network dimension answer: up, down or unknown."""
    if value is None:
        return "unknown"
    if isinstance(value, str):
        wanted = value.strip().lower()
        if wanted in ("up", "online", "reachable"):
            return "up"
        if wanted in ("down", "offline", "unreachable"):
            return "down"
        if wanted == "unknown":
            return "unknown"
    raise ValueError(
        f"a network status must be up, down or unknown, "
        f"got {value!r}")


def normalize_record_id(value: Any) -> str:
    """The canonical registry record id a word names."""
    if isinstance(value, str):
        wanted = value.strip()
        if wanted and all(ch in _ID_CHARS for ch in wanted):
            return wanted
    raise ValueError(
        f"a record id must be a non-empty word of letters, "
        f"digits, dashes, underscores and dots, got {value!r}")


# ---------------------------------------------------------------------
# The failure: one thing that went down, held as data.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DegradationFailure:
    """One failure, as data: its kind and the evidence words for it.

    ``kind`` is the closed vocabulary of three.
    ``detail`` is the evidence in plain words (the
    probe own words, the board own words) or an
    empty string when no detail was given - a
    failure never invents a detail. What the
    failure loses and what still stands are the
    held per-kind data, never written per failure.
    """

    kind: str
    detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "kind", normalize_failure_kind(self.kind))
        if not isinstance(self.detail, str):
            raise ValueError(
                f"a failure detail must be text, got {self.detail!r}")
        object.__setattr__(self, "detail", self.detail.strip())

    @property
    def phrase(self) -> str:
        return FAILURE_PHRASES[self.kind]

    @property
    def lost(self) -> Tuple[str, ...]:
        return LOST_CAPABILITIES[self.kind]

    @property
    def kept(self) -> Tuple[str, ...]:
        return KEPT_CAPABILITIES[self.kind]

    def to_record(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "phrase": self.phrase,
            "detail": self.detail,
            "lost": list(self.lost),
            "kept": list(self.kept),
        }


#: The shorter word for one degradation failure.
Failure = DegradationFailure

_FAILURE_KEYS = frozenset({"kind", "failure", "name", "detail", "evidence"})


def validate_failure(failure: Any) -> DegradationFailure:
    """Validate one failure into a DegradationFailure.

    Accepts a DegradationFailure, a kind word, or a
    mapping naming a ``kind`` (or ``failure`` /
    ``name``) and optionally a ``detail`` (or
    ``evidence``). Naming two spellings of one
    field with different values refuses, and
    unknown keys refuse.
    """
    if isinstance(failure, DegradationFailure):
        return failure
    if isinstance(failure, str):
        return DegradationFailure(kind=failure)
    if not isinstance(failure, dict):
        raise ValueError(f"a failure must be a mapping, got {failure!r}")
    unknown = set(failure) - _FAILURE_KEYS
    if unknown:
        raise ValueError(
            "unknown failure keys: %s" % ", ".join(sorted(unknown)))
    kind = _pick(failure, ("kind", "failure", "name"), "failure kinds")
    if kind is None:
        raise ValueError("a failure must name its kind")
    kwargs: Dict[str, Any] = {"kind": kind}
    detail = _pick(failure, ("detail", "evidence"), "failure details")
    if detail is not None:
        kwargs["detail"] = detail
    return DegradationFailure(**kwargs)


def build_failure(kind: Any, detail: Any = "") -> DegradationFailure:
    """Build one validated failure from its kind and detail."""
    return DegradationFailure(kind=kind, detail=detail)


# ---------------------------------------------------------------------
# The assessment: the judged degradation state, and the judge.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DegradationAssessment:
    """The judged state: full, degraded or unknown, with its evidence.

    ``failures`` is the known failures, held in
    roadmap order with no duplicates. ``unknowns``
    names the dimensions whose evidence was
    unknown, in roadmap dimension order (provider,
    lsp, network). ``reasons`` carries the evidence
    in plain words - why this state, never just the
    verdict. The state must agree with its own
    evidence on construction: full names no failure
    and no unknown, degraded names at least one
    failure, and unknown names no failure and at
    least one unknown - an assessment can never
    disagree with itself.
    """

    state: str
    failures: Tuple[DegradationFailure, ...] = ()
    unknowns: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()
    record_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(
                "a degradation state must be one of %s, got %r"
                % ("/".join(STATES), self.state))
        cleaned = tuple(validate_failure(item) for item in self.failures)
        ordered = tuple(
            item for kind in FAILURE_KINDS
            for item in cleaned if item.kind == kind)
        if len(ordered) != len({item.kind for item in cleaned}):
            raise ValueError("an assessment names one failure per kind")
        object.__setattr__(self, "failures", ordered)
        unknowns = tuple(str(item).strip().lower() for item in self.unknowns)
        for item in unknowns:
            if item not in ("provider", "lsp", "network"):
                raise ValueError(f"an unknown dimension is provider, lsp or network, got {item!r}")
        if len(set(unknowns)) != len(unknowns):
            raise ValueError("an assessment names each unknown dimension once")
        object.__setattr__(self, "unknowns", unknowns)
        reasons = tuple(_clean_text(item, "a reason") for item in self.reasons)
        object.__setattr__(self, "reasons", reasons)
        if self.state == "full" and (ordered or unknowns):
            raise ValueError("a full assessment names no failure and no unknown")
        if self.state == "degraded" and not ordered:
            raise ValueError("a degraded assessment names at least one failure")
        if self.state == "unknown" and (ordered or not unknowns):
            raise ValueError("an unknown assessment names no failure and at least one unknown")
        if self.record_id is not None:
            object.__setattr__(self, "record_id", normalize_record_id(self.record_id))

    @property
    def failure_kinds(self) -> Tuple[str, ...]:
        return tuple(item.kind for item in self.failures)

    @property
    def lost(self) -> Tuple[str, ...]:
        """Everything the known failures take away, in roadmap order."""
        result: List[str] = []
        for item in self.failures:
            for phrase in item.lost:
                if phrase not in result:
                    result.append(phrase)
        return tuple(result)

    @property
    def kept(self) -> Tuple[str, ...]:
        """What still stands under every known failure, in roadmap order."""
        result: List[str] = []
        for item in self.failures:
            for phrase in item.kept:
                if phrase not in result:
                    result.append(phrase)
        return tuple(result)

    def to_record(self) -> Dict[str, Any]:
        return {
            "type": "degradation_assessment",
            "slice": OFFLINE_GRACE_SLICE,
            "record_id": self.record_id,
            "state": self.state,
            "failures": [item.to_record() for item in self.failures],
            "failure_kinds": list(self.failure_kinds),
            "unknowns": list(self.unknowns),
            "lost": list(self.lost),
            "kept": list(self.kept),
            "reasons": list(self.reasons),
        }


#: The shorter word for a degradation assessment.
Assessment = DegradationAssessment

_EVIDENCE_KEYS = frozenset({
    "provider", "provider_status", "lsp", "lsp_status",
    "network", "network_status", "net", "net_status",
    "provider_detail", "lsp_detail", "network_detail",
})


def judge_degradation(evidence: Any) -> DegradationAssessment:
    """Judge the degradation state from given evidence, mechanically.

    ``evidence`` is a mapping naming, per dimension,
    the answer that dimension gave: ``provider``
    (or ``provider_status``) in M-039 board words,
    ``lsp`` (or ``lsp_status``) as up / down /
    unknown, and ``network`` (or ``network_status``
    / ``net``) as up / down / unknown. Optional
    ``provider_detail`` / ``lsp_detail`` /
    ``network_detail`` words ride the matching
    failure as its evidence detail. A dimension
    not named is unknown. Unknown keys refuse,
    and two spellings naming different answers
    refuse. The judge reads data only:

    * provider unreachable is provider_down, and
      provider needs-key is provider_down whose
      reason says the key is not held - the door
      cannot serve, stated honestly, never dressed
      up as a dead door;
    * LSP down is lsp_down; network down is
      network_down;
    * any known failure makes the state degraded;
      no failure and no unknown makes it full; no
      failure with an unknown makes it unknown.
    """
    if evidence is None:
        evidence = {}
    if not isinstance(evidence, dict):
        raise ValueError(f"degradation evidence must be a mapping, got {evidence!r}")
    unknown_keys = set(evidence) - _EVIDENCE_KEYS
    if unknown_keys:
        raise ValueError("unknown evidence keys: %s" % ", ".join(sorted(unknown_keys)))
    provider = normalize_provider_status(_pick(evidence, ("provider", "provider_status"), "provider answers"))
    lsp = normalize_lsp_status(_pick(evidence, ("lsp", "lsp_status"), "LSP answers"))
    network = normalize_network_status(_pick(evidence, ("network", "network_status", "net", "net_status"), "network answers"))
    details = {
        "provider_down": evidence.get("provider_detail") or "",
        "lsp_down": evidence.get("lsp_detail") or "",
        "network_down": evidence.get("network_detail") or "",
    }
    for key, value in details.items():
        if not isinstance(value, str):
            raise ValueError(f"a failure detail must be text, got {value!r}")
    failures: List[DegradationFailure] = []
    unknowns: List[str] = []
    reasons: List[str] = []
    if provider == "reachable":
        reasons.append("The provider answered: a provider door is reachable.")
    elif provider == "unreachable":
        failures.append(DegradationFailure(kind="provider_down", detail=details["provider_down"]))
        reasons.append("The provider did not answer: its board status is unreachable.")
    elif provider == "needs-key":
        failures.append(DegradationFailure(kind="provider_down", detail=details["provider_down"]))
        reasons.append("No provider key is held, so the provider door cannot serve: its board status is needs-key, stated as a missing key, not as a dead door.")
    else:
        unknowns.append("provider")
        reasons.append("The provider evidence is unknown: it is named unknown, never guessed up or down.")
    if lsp == "up":
        reasons.append("The language server (LSP) is up.")
    elif lsp == "down":
        failures.append(DegradationFailure(kind="lsp_down", detail=details["lsp_down"]))
        reasons.append("The language server (LSP) is down.")
    else:
        unknowns.append("lsp")
        reasons.append("The language server (LSP) evidence is unknown: it is named unknown, never guessed up or down.")
    if network == "up":
        reasons.append("The network is up.")
    elif network == "down":
        failures.append(DegradationFailure(kind="network_down", detail=details["network_down"]))
        reasons.append("The network is down.")
    else:
        unknowns.append("network")
        reasons.append("The network evidence is unknown: it is named unknown, never guessed up or down.")
    if failures:
        state = "degraded"
    elif unknowns:
        state = "unknown"
    else:
        state = "full"
    return DegradationAssessment(state=state, failures=tuple(failures), unknowns=tuple(unknowns), reasons=tuple(reasons))


# ---------------------------------------------------------------------
# The news record: one degradation change, shaped as session news.
# ---------------------------------------------------------------------


def plain_words(assessment: Any) -> str:
    """One degradation assessment, in plain words, said honestly.

    A full assessment says so and names all three
    dimensions. A degraded assessment names every
    failure and everything it lost. An unknown
    assessment says plainly that the state is not
    known and names the unknown dimensions - it
    never claims full and never claims a failure.
    """
    if not isinstance(assessment, DegradationAssessment):
        raise ValueError("plain words need a degradation assessment")
    if assessment.state == "full":
        return ("Degradation: full - the provider, the language server "
                "(LSP) and the network all answered, and nothing is lost.")
    if assessment.state == "unknown":
        return ("Degradation: unknown - no failure is known, but the "
                "evidence for %s is unknown, so the coder does not "
                "claim full and does not claim a failure."
                % ", ".join(assessment.unknowns))
    lost = "; ".join(assessment.lost)
    names = ", ".join(item.phrase for item in assessment.failures)
    return (f"Degradation: degraded - {names}. What it lost: {lost}.")


def degradation_record(assessment: Any) -> Dict[str, Any]:
    """The session-news record of one degradation assessment.

    Every judged degradation yields a record - the
    agent layer publishes this record as a session
    event, so a degradation change is announced in
    plain words in its headline, never lost as a
    mere log line. The record names the state, the
    failures, what was lost and what still stands.
    """
    if not isinstance(assessment, DegradationAssessment):
        raise ValueError("a record needs a degradation assessment")
    record = assessment.to_record()
    return {
        "type": "degradation_change",
        "session_event": "degradation_change",
        "news": True,
        "slice": OFFLINE_GRACE_SLICE,
        "record_id": record["record_id"],
        "state": record["state"],
        "failures": record["failures"],
        "failure_kinds": record["failure_kinds"],
        "unknowns": record["unknowns"],
        "lost": record["lost"],
        "kept": record["kept"],
        "reasons": record["reasons"],
        "headline": plain_words(assessment),
    }


# ---------------------------------------------------------------------
# The registry model: a session degradation records, ids deterministic.
# ---------------------------------------------------------------------


class DegradationRegistry:
    """An in-memory, storage-neutral degradation registry.

    Assessments are held in the order judged, under
    deterministic ``grace-N`` ids: a caller-supplied
    id is used as given (a duplicate refuses), and
    an unsupplied id is the next ``grace-N`` in
    sequence, skipping any number a supplied id
    already took - no randomness a test cannot pin.
    Storage beyond memory is the agent layer concern;
    this model is neutral.
    """

    def __init__(self) -> None:
        self._records: Dict[str, DegradationAssessment] = {}
        self._next = 1

    def _fresh_id(self) -> str:
        while f"grace-{self._next}" in self._records:
            self._next += 1
        record_id = f"grace-{self._next}"
        self._next += 1
        return record_id

    def register(self, assessment: Any) -> DegradationAssessment:
        """Hold one assessment, under its id or a fresh deterministic one."""
        if not isinstance(assessment, DegradationAssessment):
            raise ValueError("the registry holds degradation assessments")
        if assessment.record_id is None:
            assessment = replace(assessment, record_id=self._fresh_id())
        elif assessment.record_id in self._records:
            raise ValueError(f"a degradation record named {assessment.record_id!r} already exists")
        self._records[assessment.record_id] = assessment
        return assessment

    def judge_and_register(self, evidence: Any) -> DegradationAssessment:
        """Judge evidence and hold the assessment, in one move."""
        return self.register(judge_degradation(evidence))

    def get(self, record_id: Any) -> DegradationAssessment:
        """The assessment one id names; an unknown id raises KeyError."""
        wanted = normalize_record_id(record_id)
        if wanted not in self._records:
            raise KeyError(f"unknown degradation record: {wanted!r}")
        return self._records[wanted]

    def list_records(self) -> Tuple[DegradationAssessment, ...]:
        """Every held assessment, in the order judged, as a tuple."""
        return tuple(self._records.values())

    def __len__(self) -> int:
        return len(self._records)

    def record(self, record_id: Any) -> Dict[str, Any]:
        """One held assessment session-news record."""
        return degradation_record(self.get(record_id))


#: The shorter word for the degradation registry.
Registry = DegradationRegistry


# ---------------------------------------------------------------------
# The /grace surface: one parser + formatters, both roads.
# ---------------------------------------------------------------------


def format_failure(failure: Any) -> str:
    """One failure, in plain words: what it lost, stated whole."""
    current = validate_failure(failure)
    lines = [f"{current.kind}: {current.phrase}."]
    if current.detail:
        lines.append(f"  evidence: {current.detail}")
    for phrase in current.lost:
        lines.append(f"  lost: {phrase}")
    for phrase in current.kept:
        lines.append(f"  still stands: {phrase}")
    return "\n".join(lines)


def format_failures() -> str:
    """Every failure kind this layer speaks of, in roadmap order."""
    lines = [f"Degraded grace failures: {len(FAILURE_KINDS)} kinds."]
    for kind in FAILURE_KINDS:
        lines.append(f"  {format_failure(DegradationFailure(kind=kind))}")
    return "\n".join(lines)


def format_assessment(assessment: Any) -> str:
    """One degradation assessment, in plain words: lost always stated."""
    if not isinstance(assessment, DegradationAssessment):
        raise ValueError("formatting needs a degradation assessment")
    name = assessment.record_id or "assessment"
    lines = [f"{name}: {plain_words(assessment)}"]
    for reason in assessment.reasons:
        lines.append(f"  {reason}")
    for phrase in assessment.lost:
        lines.append(f"  lost: {phrase}")
    for phrase in assessment.kept:
        lines.append(f"  still stands: {phrase}")
    return "\n".join(lines)


def _assessments_from(source: Any) -> Tuple[DegradationAssessment, ...]:
    if source is None:
        return ()
    if isinstance(source, DegradationRegistry):
        return source.list_records()
    if isinstance(source, DegradationAssessment):
        return (source,)
    if isinstance(source, (list, tuple)):
        result = []
        for item in source:
            if not isinstance(item, DegradationAssessment):
                raise ValueError("held records must be degradation assessments")
            result.append(item)
        return tuple(result)
    raise ValueError("records must be a registry, assessment or list")


def format_grace_record(record: Any) -> str:
    """One degradation news record as its plain headline."""
    if isinstance(record, dict) and record.get("type") == "degradation_change":
        return str(record["headline"])
    raise ValueError("format_grace_record needs a degradation record")


#: The record formatter under its short name.
format_record = format_grace_record


def format_grace_screen(source: Any = None) -> str:
    """The whole slice, in plain words, for /grace."""
    records = _assessments_from(source)
    lines = ["Offline and degraded grace (M-115) - " + PLAIN_EXPLANATION, ""]
    if not records:
        lines.append("Degradation records: no records held. No degradation change is held for this session.")
    else:
        lines.append(f"Degradation records: {len(records)} held.")
        for item in records:
            lines.append(f"  {format_assessment(item).splitlines()[0]}")
    lines.append("")
    lines.append(USAGE)
    return "\n".join(lines)


_GRAMMAR_WORDS = ("show", "failures")


def parse_grace_args(args: Any) -> Tuple[str, Optional[str]]:
    """Parse the /grace grammar both surfaces share.

    No words (or ``show``) shows the held records;
    ``show <record>`` and a bare record id show one
    record; ``failures`` shows the failure kinds
    alone. A grammar word in the wrong shape is a
    usage error naming the grammar, never a record
    id. Returns ``(action, target-or-None)``.
    """
    text = (args or "").strip() if isinstance(args, str) or args is None else None
    if text is None:
        raise ValueError(USAGE)
    if not text or text.lower() == "show":
        return ("show", None)
    if text.lower() == "failures":
        return ("failures", None)
    words = text.split()
    head = words[0].lower()
    if head == "show" and len(words) == 2:
        if words[1].lower() in _GRAMMAR_WORDS:
            raise ValueError(USAGE)
        try:
            return ("show", normalize_record_id(words[1]))
        except ValueError:
            raise ValueError(USAGE) from None
    if head in _GRAMMAR_WORDS or len(words) != 1:
        raise ValueError(USAGE)
    try:
        return ("show", normalize_record_id(words[0]))
    except ValueError:
        raise ValueError(USAGE) from None
