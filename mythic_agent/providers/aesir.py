"""Project Aesir provider adapter (All-Features slice M-025).

Project Aesir is Volmarr's own Mojo inference engine. This adapter
aims Mythic at it — *its API as it stands*, taken from Aesir's own
``docs/NATIVE_SERVICE.md``, ``docs/API_SUPPORT_MATRIX_V1.md`` and
``scripts/fixtures/api_contract_v1.json`` (read at slice time) — so
the ecosystem eats its own cooking.

Aesir's server has two doors, chosen at ``aesir serve`` time:

* **The native door (this adapter's home)** — default
  ``127.0.0.1:18434``, loopback only, Bearer authentication with a
  key the server reads from a key file (``aesir keygen``). Routes:
  ``GET /health`` / ``/health/live`` / ``/health/ready``,
  ``POST /v1/generate`` (Aesir's flat native generation shape),
  ``GET /v1/models`` and the OpenAI-subset routes
  ``POST /v1/chat/completions`` / ``POST /v1/completions``.
  :meth:`AesirProvider.chat` speaks the chat route;
  :meth:`AesirProvider.native_generate` speaks the native one.
* **The Ollama-compatible door** — started with ``--ollama`` on
  ``127.0.0.1:11434``, no authentication, Ollama-shaped routes.
  :meth:`AesirProvider.ollama_snapshot` reads its version, catalog
  and resident model so a user running that door is seen honestly
  too. Chat through that door is the Ollama provider's road.

The honesty rules — capability limits reported *as Aesir reports
them*, never widened:

* Aesir serves **one resident model at a time**. ``GET /v1/models``
  lists the *catalog* (registered weights); catalog visibility is
  not readiness and not inference capacity. Only the resident model
  (named by ``/health/ready``) can generate, so
  :meth:`ensure_model` checks residency, not catalog membership.
* ``capabilities()`` is therefore: streaming **True** (the native
  and OpenAI routes stream as NDJSON/SSE subsets), tool_calling
  **False** (Aesir's only tool support is one zero-argument function
  on the Gemma template — not general tool calling, and this
  adapter refuses ``tools=`` rather than pretending), vision
  **False** (multimodal messages are rejected by Aesir), json_mode
  **False** (the only structured output Aesir offers is a strict
  Boolean schema subset — :meth:`chat` passes exactly that shape
  through and refuses every other ``response_format``).
* :meth:`reported_capabilities` returns the full Aesir-shaped
  picture, including the live backend/profile/context the server
  itself reports when it is reachable.

The service key never appears in error text (the inherited
redaction holds), is read from the ``AESIR_API_KEY`` environment
variable or passed explicitly, and can be loaded from an Aesir key
file via ``api_key_file=`` — the file's contents are read once at
construction and never logged.
"""


from __future__ import annotations

__all__ = [
    "AesirProvider",
    "Any",
    "Callable",
    "Optional",
    "Provider",
    "ProviderError",
    "ProviderNotConfigured",
]

import os
from typing import Any, Callable, Optional

try:
    import httpx2
except ImportError:  # pragma: no cover - declared fallback pattern
    import httpx as httpx2  # type: ignore[no-redef]

from .base import Provider, ProviderError, ProviderNotConfigured
from .openai_compat import OpenAICompatProvider

#: The one structured-output shape Aesir's OpenAI routes accept
#: (API matrix S23): a strict Boolean JSON schema.
_BOOLEAN_SCHEMA = {"type": "boolean"}


def _is_boolean_response_format(value: Any) -> bool:
    """True only for Aesir's strict Boolean ``response_format`` subset."""
    if not isinstance(value, dict) or value.get("type") != "json_schema":
        return False
    schema_block = value.get("json_schema")
    if not isinstance(schema_block, dict):
        return False
    if schema_block.get("strict") is not True:
        return False
    name = schema_block.get("name")
    if not isinstance(name, str) or not name:
        return False
    return schema_block.get("schema") == _BOOLEAN_SCHEMA


class AesirProvider(OpenAICompatProvider):
    """Project Aesir native-door adapter (OpenAI-subset chat shape).

    ``name = "aesir"``, ``api_key_env = "AESIR_API_KEY"``,
    ``default_model = "aesir-local"`` — a placeholder, like the other
    local doors: Aesir serves whichever single model it was launched
    with, and :meth:`discover` reports that model's real name.
    """

    name = "aesir"
    default_model = "aesir-local"
    api_key_env = "AESIR_API_KEY"

    #: Class-level default endpoint (the native door's ``/v1`` root).
    base_url_default = "http://127.0.0.1:18434/v1"

    #: Default base of Aesir's Ollama-compatible door.
    ollama_base_default = "http://127.0.0.1:11434"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key_file: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        transport: Optional[Callable[..., tuple[int, Any]]] = None,
    ) -> None:
        if api_key is None and api_key_file is not None:
            api_key = self._read_key_file(api_key_file)
        super().__init__(api_key=api_key, model=model, base_url=base_url,
                         timeout=timeout, max_retries=max_retries,
                         transport=transport)
        self.ollama_base_url = (
            ollama_base_url or self.ollama_base_default).rstrip("/")

    # -- key custody ---------------------------------------------------------

    @staticmethod
    def _read_key_file(path: str) -> str:
        """Read an Aesir service key file; never echo its contents.

        Aesir key files hold 32..256 key characters plus at most one
        trailing newline. A missing/unreadable file is a
        :class:`ProviderNotConfigured` carrying the ``aesir keygen``
        remedy — the key itself is never part of any message.
        """
        try:
            with open(path, encoding="utf-8") as handle:
                key = handle.read().strip()
        except OSError as exc:
            raise ProviderNotConfigured(
                f"Aesir service key file {path!r} could not be read "
                f"({type(exc).__name__}). Create one with "
                "`aesir keygen <path>` and start the service with "
                "`--api-key-file <path>`.") from exc
        if not key:
            raise ProviderNotConfigured(
                f"Aesir service key file {path!r} is empty. Create "
                "one with `aesir keygen <path>`.")
        return key

    # -- Provider protocol ----------------------------------------------------

    def capabilities(self) -> dict[str, bool]:
        # As Aesir reports them (see the module docstring): streaming
        # yes; general tool calling, vision and general JSON mode no.
        return {"streaming": True, "tool_calling": False,
                "vision": False, "json_mode": False}

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Chat via Aesir's ``POST /v1/chat/completions`` route.

        Only the knobs Aesir's OpenAI subset accepts are forwarded
        (``temperature``, ``top_p``, ``seed``, ``max_tokens``).
        ``tools=`` / ``tool_choice=`` are refused — Aesir's tool
        support is a single zero-argument Gemma function, not the
        general shape — and ``response_format=`` is forwarded only
        when it is exactly Aesir's strict Boolean schema subset.
        A ``tool``-role or non-string message content is refused up
        front: Aesir's chat route rejects those shapes itself, and
        an early honest refusal beats a wire round-trip.
        """
        messages = self.validate_messages(messages)
        for message in messages:
            if message.get("role") == "tool":
                raise ProviderError(
                    "aesir chat does not accept tool-role messages: "
                    "Aesir has no tool-result continuation protocol "
                    "(its only tool support is one zero-argument "
                    "Gemma function it executes no part of).")
            if not isinstance(message.get("content"), str):
                raise ProviderError(
                    "aesir chat accepts string message content only: "
                    "Aesir rejects multimodal/array content (vision "
                    "is not supported).")
        if "tools" in kwargs or "tool_choice" in kwargs:
            raise ProviderError(
                "aesir does not offer general tool calling: its "
                "OpenAI route accepts at most one zero-argument "
                "function on the Gemma template, which this adapter "
                "does not dress up as tool_calling. capabilities() "
                "reports tool_calling as False for this reason.")
        if "response_format" in kwargs and not _is_boolean_response_format(
                kwargs["response_format"]):
            raise ProviderError(
                "aesir structured output is limited to the strict "
                "Boolean json_schema subset "
                "({'type': 'json_schema', 'json_schema': {'name': "
                "..., 'strict': True, 'schema': {'type': "
                "'boolean'}}}); other response_format shapes are "
                "refused, never silently dropped.")
        return super().chat(messages, **kwargs)

    # -- transport seams -------------------------------------------------------

    def _root(self) -> str:
        """The native door's host root (``base_url`` minus ``/v1``)."""
        return self.base_url.rsplit("/v1", 1)[0].rstrip("/")

    def _get_at(self, url: str) -> tuple[int, Any]:
        """GET ``url`` with auth headers; single GET seam for tests.

        A transport failure maps to :class:`ProviderError` saying
        Aesir is unreachable at that address plus the start remedy —
        never a bare socket error. A non-200 status is the server's
        own answer and is returned, not raised.
        """
        try:
            with httpx2.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
        except httpx2.HTTPError as exc:
            raise ProviderError(
                f"aesir is unreachable at {url}: "
                f"{type(exc).__name__}. {self._start_remedy()}") from exc
        try:
            return response.status_code, response.json()
        except ValueError:
            if response.status_code == 200:
                raise ProviderError(
                    f"aesir returned malformed JSON from {url}.") from None
            return response.status_code, None

    def _get_json(self, path: str) -> tuple[int, Any]:
        """GET ``base_url + path`` through :meth:`_get_at`."""
        return self._get_at(self.base_url + path)

    def _get_root(self, path: str) -> tuple[int, Any]:
        """GET ``<host root> + path`` (the health routes live there)."""
        return self._get_at(self._root() + path)

    def _start_remedy(self) -> str:
        return ("Start Aesir with `aesir serve <model> --accel cuda "
                "--api-key-file <key-file>` (native door, default "
                "http://127.0.0.1:18434), then try again.")

    # -- native-door surface ---------------------------------------------------

    def health(self) -> bool:
        """True when the resident session reports ready.

        Probes the authenticated ``GET /health/ready`` route: HTTP
        200 with ``ready: true`` is the only healthy answer; a 503,
        a transport failure, or anything else is honestly not-ready.
        """
        try:
            status, body = self._get_root("/health/ready")
        except ProviderError:
            return False
        return (status == 200 and isinstance(body, dict)
                and body.get("ready") is True)

    def ready(self) -> dict[str, Any]:
        """The server's own ``/health/ready`` record.

        Raises :class:`ProviderError` when the service answers
        not-ready (503) — the record it sent is named in the error
        only by its status, never dressed up as a snapshot.
        """
        status, body = self._get_root("/health/ready")
        if status != 200 or not isinstance(body, dict):
            raise ProviderError(
                f"aesir at {self._root()} is not ready (HTTP "
                f"{status}). {self._start_remedy()}")
        return body

    def live(self) -> dict[str, Any]:
        """The server's ``/health/live`` process-liveness record."""
        status, body = self._get_root("/health/live")
        if status != 200 or not isinstance(body, dict):
            raise ProviderError(
                f"aesir at {self._root()} did not answer its "
                f"liveness route (HTTP {status}). "
                + self._start_remedy())
        return body

    def catalog_models(self) -> list[str]:
        """Model ids in Aesir's catalog (``GET /v1/models``).

        Catalog visibility is *not* readiness: Aesir lists every
        registered weight manifest, while only the resident model
        can generate (see :meth:`resident_model`).
        """
        status, body = self._get_json("/models")
        if status != 200:
            raise ProviderError(
                f"aesir at {self.base_url} answered HTTP {status} "
                "for its model catalog.")
        if not isinstance(body, dict) or not isinstance(
                body.get("data"), list):
            return []
        return [entry["id"] for entry in body["data"]
                if isinstance(entry, dict)
                and isinstance(entry.get("id"), str) and entry["id"]]

    def list_models(self) -> list[str]:
        """Catalog model ids; an empty catalog is an honest error."""
        names = self.catalog_models()
        if not names:
            raise ProviderError(
                f"aesir at {self.base_url} reported an empty model "
                "catalog. Import a model with "
                "`aesir create <name> --modelfile <file> --model "
                "<file.gguf>`, then try again.")
        return names

    def resident_model(self) -> Optional[str]:
        """The one model Aesir currently has loaded, or None.

        Read from the server's own readiness record; a not-ready
        service has no resident model to name, so None is honest.
        """
        try:
            record = self.ready()
        except ProviderError:
            return None
        model = record.get("model")
        return model if isinstance(model, str) and model else None

    def model_present(self, name: str) -> bool:
        """True when ``name`` is in Aesir's catalog.

        Presence means registered, *not* loaded — generation also
        needs residency (:meth:`ensure_model`).
        """
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model name given to look for.")
        return wanted in self.catalog_models()

    def ensure_model(self, name: str) -> str:
        """Return ``name`` if it is the resident model; else refuse.

        Aesir serves one resident model at a time and has no hot
        swap, so a catalog model that is not resident gets an
        honest not-resident error carrying the restart remedy, and
        a model outside the catalog gets a not-present error
        carrying the import remedy.
        """
        wanted = (name or "").strip()
        if not wanted:
            raise ProviderError("No model configured for aesir provider")
        resident = self.resident_model()
        if resident == wanted:
            return wanted
        if wanted in self.catalog_models():
            raise ProviderError(
                f"Model {wanted!r} is in Aesir's catalog at "
                f"{self.base_url} but is not the resident model "
                f"(resident: {resident!r}). Aesir serves one model "
                "at a time with no hot swap; restart it with "
                f"`aesir serve {wanted} --accel cuda "
                "--api-key-file <key-file>`.")
        raise ProviderError(
            f"Model {wanted!r} is not present in Aesir's catalog "
            f"at {self.base_url}. Import it with `aesir create "
            f"{wanted} --modelfile <file> --model <file.gguf>`, "
            "then serve it.")

    def native_generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """One native generation via ``POST /v1/generate``.

        Accepts Aesir's own flat fields only (``system``,
        ``max_tokens``, ``timeout_ms``, ``temperature``, ``top_k``,
        ``top_p``, ``min_p``, ``repeat_penalty``, ``seed``);
        anything else is refused before the wire — Aesir rejects
        unknown fields itself, and an early refusal names the
        field. Returns the server's full record (text,
        finish_reason, token counts, backend, timings, model
        identity) exactly as Aesir reports it.
        """
        text_prompt = (prompt or "").strip()
        if not text_prompt:
            raise ProviderError("aesir native generation needs a prompt")
        allowed = ("system", "max_tokens", "timeout_ms", "temperature",
                   "top_k", "top_p", "min_p", "repeat_penalty", "seed")
        unknown = sorted(set(kwargs) - set(allowed))
        if unknown:
            raise ProviderError(
                "aesir /v1/generate does not accept field(s) "
                + ", ".join(unknown)
                + "; its accepted fields are: " + ", ".join(allowed)
                + ".")
        payload: dict[str, Any] = {"prompt": prompt}
        for knob in allowed:
            if knob in kwargs:
                payload[knob] = kwargs[knob]
        _status, body = self._request_with_retries(
            "/generate", payload, self._headers())
        if not isinstance(body, dict) or not isinstance(
                body.get("text"), str):
            raise ProviderError(
                "aesir returned a malformed native generation record.")
        return body

    def reported_capabilities(self) -> dict[str, Any]:
        """Capability limits as Aesir reports them, live where possible.

        The static half is Aesir's documented v1 subset (API support
        matrix); the live half — backend, profile, context, resident
        model and digest — is filled from the server's own
        readiness record when it answers, and stays ``None`` (an
        honest unknown) when it does not.
        """
        report: dict[str, Any] = {
            "streaming": True,
            "tool_calling": False,
            "tool_calling_note": (
                "single zero-argument Gemma function only; not "
                "general tool calling, no tool execution"),
            "vision": False,
            "json_mode": False,
            "json_mode_note": (
                "strict Boolean json_schema subset only"),
            "embeddings": False,
            "resident_models": 1,
            "catalog_is_readiness": False,
            "reachable": False,
            "backend": None,
            "profile": None,
            "context": None,
            "model": None,
            "model_digest": None,
        }
        try:
            record = self.ready()
        except ProviderError:
            return report
        report["reachable"] = True
        for key, field in (("backend", "backend"),
                           ("profile", "profile"),
                           ("context", "context"),
                           ("model", "model"),
                           ("model_digest", "digest")):
            value = record.get(field)
            if value is not None:
                report[key] = value
        return report

    def discover(self) -> dict[str, Any]:
        """One-call snapshot of the native door.

        An unreachable or not-ready service raises the honest
        unreachable/not-ready error — no snapshot is dressed up as
        success. A catalog failure after a ready probe degrades the
        catalog to an empty list (the resident session still
        stands), mirroring Aesir's own rule that catalog errors do
        not poison the resident session.
        """
        record = self.ready()
        try:
            catalog = self.catalog_models()
        except ProviderError:
            catalog = []
        return {"host": self._root(),
                "base_url": self.base_url,
                "mode": "native",
                "ready": True,
                "backend": record.get("backend"),
                "profile": record.get("profile"),
                "context": record.get("context"),
                "resident": record.get("model"),
                "catalog": catalog}

    # -- Ollama-compatible door -------------------------------------------------

    def ollama_snapshot(self) -> dict[str, Any]:
        """Snapshot of Aesir's ``--ollama`` door, when it is running.

        Reads ``GET /api/version`` (whose answer identifies the
        Aesir adapter, ``0.1.0-aesir``), ``GET /api/tags`` (the
        catalog) and ``GET /api/ps`` (the resident model) from the
        Ollama-door base. An unreachable door raises the honest
        unreachable error carrying that door's start remedy.
        """
        status, version_body = self._get_at(
            self.ollama_base_url + "/api/version")
        if status != 200 or not isinstance(version_body, dict):
            raise ProviderError(
                f"aesir's Ollama-compatible door is unreachable at "
                f"{self.ollama_base_url} (HTTP {status}). Start it "
                "with `aesir serve <model> --accel cuda --ollama` "
                "(default http://127.0.0.1:11434), then try again.")
        _s, tags_body = self._get_at(self.ollama_base_url + "/api/tags")
        _s, ps_body = self._get_at(self.ollama_base_url + "/api/ps")

        def _names(body: Any) -> list[str]:
            if not isinstance(body, dict) or not isinstance(
                    body.get("models"), list):
                return []
            return [entry["name"] for entry in body["models"]
                    if isinstance(entry, dict)
                    and isinstance(entry.get("name"), str)
                    and entry["name"]]

        return {"host": self.ollama_base_url,
                "mode": "ollama",
                "version": version_body.get("version"),
                "catalog": _names(tags_body),
                "resident": _names(ps_body)}
