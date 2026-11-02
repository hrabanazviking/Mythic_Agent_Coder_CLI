"""Provider health board (All-Features roadmap slice M-039).

Part II — The Provider Ocean — grows its health road here.
``mythic doctor --live`` used to probe THE configured door
only (``mythic_agent.doctor.check_provider_live`` — one door,
one result, and it stays). Nothing walked the M-019
registry's doors to report each one's health side by side.
This slice is that board.

What the board is:

* One entry per M-019 registry door, in registry order,
  carrying the door's **status** (``reachable`` /
  ``unreachable`` / ``needs-key`` / ``unknown``), its
  **latency** in milliseconds, and its **last error** — plus
  the door's M-032 key-custody state and, where a session's
  M-036 WeatherBoard has seen the door, its remembered
  weather state.
* The live road is ``mythic doctor --live``: the board is
  probed and printed there, and carried in ``--json`` output
  as a ``provider_health`` record. ``Agent.provider_health()``
  answers the same board for in-session surfaces, reusing
  the crew's shared weather board.

Honesty rules, enforced here and pinned by the slice's tests:

* **A door never probed reports unknown, never reachable.**
  Latency is measured around a real probe or it is None —
  never invented. The last error is the probe's own words;
  a door that was not probed has no last error.
* **Remote doors without a key are never probed.** A remote
  door whose key is not held reports ``needs-key`` with its
  M-032 custody state (Kista / environment / plaintext /
  missing) instead of a fake reachability — the board does
  not spend a request it cannot authenticate, and does not
  dress a missing key up as a dead door.
* **Local doors probe their live endpoints.** A compatible
  door answers at its ``/models``, Ollama at its
  ``/api/tags``, and Aesir at its authenticated
  ``/health/ready`` (HTTP 200 with ``ready: true`` is the
  only healthy answer, exactly as Aesir's own adapter reads
  it). A non-200 answer is unreachable with the status as
  its last error; a transport failure is unreachable with
  the failure's own words (redacted, bounded).
* **Native-SDK doors report unknown.** Anthropic and Google
  record endpoint null in the registry — their SDKs own the
  service address — so the board invents no address to
  probe: the entry says ``unknown`` and says why. (The
  configured door, whichever it is, keeps its own live
  check in ``mythic doctor --live``.)
* **No key value ever rides the board.** Custody is a state
  and a presence flag; the key itself is used only as the
  probe's Authorization header and appears in no entry,
  record, or formatted line.
"""

from __future__ import annotations

__all__ = [
    "HEALTH_SLICE",
    "PLAIN_EXPLANATION",
    "STATUSES",
    "Any",
    "Board",
    "Callable",
    "Dict",
    "HealthEntry",
    "List",
    "Optional",
    "Tuple",
    "build_board",
    "default_prober",
    "format_board",
    "probe_url_for",
]

import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from .key_custody import is_reference, load_vault, resolve_reference, vault_path
from .provider_registry import ProviderDef, ProviderRegistry, load_registry

#: The slice that owns this module.
HEALTH_SLICE = "M-039"

#: The board's status vocabulary, in board order.
STATUSES: Tuple[str, ...] = ("reachable", "unreachable", "needs-key", "unknown")

#: The default per-door probe budget, in seconds. A health
#: probe stays short; turn timeouts are a separate concern.
DEFAULT_TIMEOUT = 5.0

#: Provider health explained in plain words — the sentence
#: every surface shows.
PLAIN_EXPLANATION = (
    "Provider health board: every door in the provider "
    "registry, side by side — reachable, how long it took to "
    "answer, and the last error it gave, in its own words. A "
    "door that was never probed says unknown, never "
    "reachable, and carries no latency and no error. A "
    "remote door whose key is not held says needs-key and "
    "shows where its key should live (Kista) instead of "
    "pretending to be dead. Doors whose address belongs to "
    "their vendor's own software kit say unknown, because no "
    "address is invented for them."
)


@dataclass(frozen=True)
class HealthEntry:
    """One door's health: status, measured latency, last error.

    ``latency_ms`` is a measured number or None (never
    invented). ``last_error`` is the probe's own words or
    None — a door that was not probed, or that answered, has
    no last error. ``custody`` is the M-032 custody state for
    the door's key (``kista`` / ``environment`` / ``plaintext``
    / ``missing`` / ``not-needed``) and ``key_present`` whether
    a key is held; no field ever carries a key value.
    ``remembered_state`` is the M-036 weather board's state
    for this door where a session board has seen it, else
    None.
    """

    provider: str
    title: str
    locality: str
    dialect: str
    endpoint: Optional[str]
    status: str
    probed: bool
    latency_ms: Optional[float]
    last_error: Optional[str]
    custody: str
    key_present: bool
    remembered_state: Optional[str]
    detail: str

    def record(self) -> Dict[str, Any]:
        """This entry as a plain mapping."""
        return {
            "provider": self.provider,
            "title": self.title,
            "locality": self.locality,
            "dialect": self.dialect,
            "endpoint": self.endpoint,
            "status": self.status,
            "probed": self.probed,
            "latency_ms": self.latency_ms,
            "last_error": self.last_error,
            "custody": self.custody,
            "key_present": self.key_present,
            "remembered_state": self.remembered_state,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Board:
    """The whole board: one entry per registry door."""

    entries: Tuple[HealthEntry, ...]
    generated_at: float

    def entry(self, provider: str) -> HealthEntry:
        """The entry for *provider* (KeyError if not a door)."""
        for entry in self.entries:
            if entry.provider == provider:
                return entry
        raise KeyError(f"no provider {provider!r} on the health board")

    def counts(self) -> Dict[str, int]:
        """How many doors stand in each status, in board order."""
        counts = {status: 0 for status in STATUSES}
        for entry in self.entries:
            counts[entry.status] += 1
        return counts

    def record(self) -> Dict[str, Any]:
        """The board as a plain mapping (the ``--json`` shape)."""
        return {
            "slice": HEALTH_SLICE,
            "generated_at": self.generated_at,
            "counts": self.counts(),
            "entries": [entry.record() for entry in self.entries],
        }


# ----------------------------------------------------------------------
# Key custody for a registry door (M-032 states, never values)
# ----------------------------------------------------------------------


def _key_state(provider: ProviderDef, config: Dict[str, Any], *,
               environ: Any, vault_file: Any) -> Tuple[str, bool, Optional[str]]:
    """(custody, present, key) for *provider* — key stays private.

    The registry door's own ``api_key_env`` names its key. A
    config ``api_keys`` entry stored under the door's endpoint
    answers first (a Kista reference resolves through Kista;
    legacy plaintext is itself), then Kista's vault file under
    the key's own name, then the environment. A malformed
    stored reference raises, exactly as M-032's custody read
    does — a custody that cannot be read truthfully surfaces.
    """
    if provider.auth_style == "none" or not provider.api_key_env:
        return "not-needed", True, None
    env_name = provider.api_key_env
    endpoint = provider.endpoint
    stored_map = config.get("api_keys") or {}
    if endpoint and isinstance(stored_map, dict) and endpoint in stored_map:
        stored = stored_map[endpoint]
        if is_reference(stored):
            key = resolve_reference(stored, environ=environ,
                                    vault_file=vault_file)
            return "kista", key is not None, key
        if isinstance(stored, str) and stored:
            return "plaintext", True, stored
    path = vault_path(vault_file, environ)
    if path is not None:
        vault = load_vault(path)
        if vault.get(env_name):
            return "kista", True, vault[env_name]
    candidate = environ.get(env_name) if environ is not None else None
    if candidate:
        return "environment", True, candidate
    return "missing", False, None


# ----------------------------------------------------------------------
# Probing — one honest GET per door
# ----------------------------------------------------------------------


def probe_url_for(provider: ProviderDef) -> Optional[str]:
    """The URL a live probe GETs for *provider*, or None.

    Compatible doors answer at ``<endpoint>/models``, Ollama
    at ``<endpoint>/api/tags``, Aesir at its host root's
    ``/health/ready``. Native-SDK doors have no URL — their
    SDK owns the address and none is invented.
    """
    endpoint = provider.endpoint
    if endpoint is None:
        return None
    base = endpoint.rstrip("/")
    if provider.dialect == "ollama_native":
        return base + "/api/tags"
    if provider.dialect == "aesir_native":
        root = base.rsplit("/v1", 1)[0] if base.endswith("/v1") else base
        return root + "/health/ready"
    return base + "/models"


def default_prober(url: str, headers: Dict[str, str],
                   timeout: float) -> Tuple[int, str]:
    """GET *url*; return (HTTP status, body text).

    A non-200 HTTP answer is the server's own answer and is
    returned, not raised. A transport failure raises, and the
    board records the failure's own words as the last error.
    """
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            return reply.status, reply.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return exc.code, body


def _redacted_error(text: str) -> str:
    """The probe failure's own words, redacted and bounded."""
    try:
        from .redaction import redact_text
        text = redact_text(text)
    except Exception:
        pass
    return text[:200]


def _probe(provider: ProviderDef, url: str, key: Optional[str], *,
           prober: Callable, timeout: float,
           clock: Callable[[], float]) -> Tuple[str, Optional[float], Optional[str]]:
    """Probe one door: (status, latency_ms, last_error)."""
    headers = {"Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    started = clock()
    try:
        status, body = prober(url, headers, timeout)
    except Exception as exc:
        latency = (clock() - started) * 1000.0
        return "unreachable", latency, _redacted_error(
            f"{type(exc).__name__}: {exc}")
    latency = (clock() - started) * 1000.0
    if status != 200:
        return "unreachable", latency, f"HTTP {status}"
    if provider.dialect == "aesir_native":
        import json
        ready = False
        try:
            parsed = json.loads(body) if body else None
            ready = isinstance(parsed, dict) and parsed.get("ready") is True
        except ValueError:
            ready = False
        if not ready:
            return ("unreachable", latency,
                    "answered /health/ready but ready is not true")
    return "reachable", latency, None


# ----------------------------------------------------------------------
# The board
# ----------------------------------------------------------------------


def build_board(config: Optional[Dict[str, Any]] = None, *,
                registry: Optional[ProviderRegistry] = None,
                weather_board: Any = None,
                prober: Optional[Callable] = None,
                environ: Any = None,
                vault_file: Any = None,
                timeout: float = DEFAULT_TIMEOUT,
                probe: bool = True,
                now: Optional[float] = None,
                clock: Optional[Callable[[], float]] = None) -> Board:
    """The health board over every registry door.

    With ``probe`` true (the ``doctor --live`` road), each
    probeable door is probed once and its latency measured;
    remote doors without a held key are not probed and report
    ``needs-key``. With ``probe`` false, no door is probed and
    every entry reports ``unknown`` — the offline board.
    ``weather_board`` is an M-036 WeatherBoard whose remembered
    state rides along where it has seen a door. ``prober`` and
    ``clock`` are injectable for tests; the clock measures
    latency (monotonic), ``now`` stamps the board.
    """
    import os

    cfg: Dict[str, Any] = config if isinstance(config, dict) else {}
    reg = registry if registry is not None else load_registry()
    env = os.environ if environ is None else environ
    probe_fn = prober if prober is not None else default_prober
    measure = clock if clock is not None else time.monotonic
    stamp = time.time() if now is None else now
    entries: List[HealthEntry] = []
    for provider in reg.providers:
        custody, present, key = _key_state(
            provider, cfg, environ=env, vault_file=vault_file)
        remembered = None
        if weather_board is not None:
            weather = weather_board.weather_for(provider.name, now=stamp)
            if weather.observed_at is not None:
                remembered = weather.effective_state(stamp)
        url = probe_url_for(provider)
        if url is None:
            status, probed, latency, last_error = "unknown", False, None, None
            detail = (
                f"{provider.title}'s address belongs to its "
                "vendor's own software kit, so the board invents "
                "no address to probe; its health is unknown to "
                "the board. (The configured door keeps its own "
                "live check in mythic doctor --live.)")
        elif not probe:
            status, probed, latency, last_error = "unknown", False, None, None
            detail = (
                f"{provider.title} was not probed — this board "
                "was built without live probing, so its health "
                "is unknown, never guessed.")
        elif provider.locality == "remote" and not present:
            status, probed, latency, last_error = "needs-key", False, None, None
            detail = (
                f"No key is held for {provider.title} — its "
                f"custody state is {custody} — so the board "
                "does not probe it and does not call it dead. "
                f"Hold its key in Kista as "
                f"kista:{provider.api_key_env} or export "
                f"{provider.api_key_env}, then probe again.")
        else:
            status, latency, last_error = _probe(
                provider, url, key, prober=probe_fn,
                timeout=timeout, clock=measure)
            probed = True
            if status == "reachable":
                detail = (
                    f"{provider.title} answered its probe at "
                    f"{url} in {latency:.0f} ms.")
            else:
                detail = (
                    f"{provider.title} did not answer its probe "
                    f"at {url}: {last_error}.")
        entries.append(HealthEntry(
            provider=provider.name, title=provider.title,
            locality=provider.locality, dialect=provider.dialect,
            endpoint=provider.endpoint, status=status,
            probed=probed, latency_ms=latency, last_error=last_error,
            custody=custody, key_present=present,
            remembered_state=remembered, detail=detail))
    return Board(entries=tuple(entries), generated_at=stamp)


def format_board(board: Board) -> str:
    """The board in plain words: one line per door, then the lesson."""
    lines = ["Provider health board:"]
    for entry in board.entries:
        latency = (f"{entry.latency_ms:.0f} ms"
                   if entry.latency_ms is not None else "not measured")
        line = (f"  {entry.provider}: {entry.status} "
                f"(latency {latency}; custody {entry.custody}"
                + (f"; remembered weather {entry.remembered_state}"
                   if entry.remembered_state else "")
                + ")")
        if entry.last_error:
            line += f" — last error: {entry.last_error}"
        lines.append(line)
    counts = board.counts()
    lines.append(
        "  Totals: " + ", ".join(
            f"{counts[status]} {status}" for status in STATUSES
            if counts[status]) + ".")
    lines.append(PLAIN_EXPLANATION)
    return "\n".join(lines)
