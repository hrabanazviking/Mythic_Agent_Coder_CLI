"""Web knowledge tools (M-059).

Part III — Code Intelligence. Web search and web fetch
as first-class tools — the roadmap's words for this
slice: "web search + fetch as first-class tools (docs,
changelogs, error lookup), results cited into the
journal."

What ships here, in ``mythic_agent/tools/web_search.py``:

* **Search.** One query goes to the *configured*
  search endpoint (the setting ``web_search_endpoint``,
  a URL template carrying ``{query}``; the shipped
  default is the keyless DuckDuckGo HTML road, so no
  API key is required and none is invented). The HTML
  answer is parsed with the standard library only, and
  DuckDuckGo's redirect wrappers are unwrapped to the
  real destination — a citation never points at a
  redirector when the real address is known.
* **Fetch.** One URL, http/https only — any other
  scheme is refused before anything leaves the
  machine. The page's readable text is extracted with
  the standard library (scripts and styles dropped,
  the ``<title>`` kept), under byte and character caps
  that name themselves in the report when they cut.
* **Citations.** Every search result carries a
  citation number; the report's ``citations`` list is
  the numbered source list, and
  :meth:`WebReport.citation_event` builds the
  ``web_citation`` session-event payload the Agent
  journals when a session is attached — the journal
  keeps *what was consulted*, with its addresses.
* **The surfaces.** ``Agent.web_search()`` /
  ``Agent.web_fetch()`` and ``/web`` on the terminal
  and TUI system-command roads, sharing this module's
  parser and formatter: ``/web search <query...>`` and
  ``/web fetch <url>``. The setting ``web_tools`` (on
  by default) closes the road plainly when the user
  says so.

Honesty rules, pinned by the slice's tests:

* **What leaves the machine is named.** Every report
  names the host the call went to and exactly what was
  sent (the query text, or the fetched URL) — the
  M-015 telemetry road: web calls are user-initiated,
  never background, never automatic.
* **Failure is a report, never an invention.** A
  non-200 answer or a transport failure comes back as
  an ``error`` report with the status or reason named
  and *no* results — the tool never fabricates a page
  it did not read.
* **A refused road stays refused.** A non-http(s)
  fetch, a search template without ``{query}``, an
  empty query: each raises plainly and nothing is
  sent.
* **Off means off.** With ``web_tools`` false, no
  transport is touched at all; the report says the
  road is closed.
"""

from __future__ import annotations

__all__ = [
    "DEFAULT_SEARCH_ENDPOINT",
    "MAX_FETCH_BYTES",
    "MAX_FETCH_CHARS",
    "MAX_RESULTS",
    "PLAIN_EXPLANATION",
    "TIMEOUT_SECONDS",
    "USAGE",
    "WEB_SLICE",
    "WebReport",
    "WebResult",
    "enabled_from_config",
    "endpoint_from_config",
    "format_web_report",
    "parse_web_args",
    "render_markdown",
    "web_fetch",
    "web_search",
]

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, urlparse

WEB_SLICE = "M-059"

#: The shipped search road: DuckDuckGo's keyless HTML
#: endpoint. ``{query}`` is replaced with the URL-encoded
#: query text; a configured template without it is refused.
DEFAULT_SEARCH_ENDPOINT = "https://html.duckduckgo.com/html/?q={query}"

#: How many results one search reports. More results
#: than this are truncated, and the report says so.
MAX_RESULTS = 10

#: Fetch bounds. A body past the byte bound is cut
#: there; extracted text past the char bound is cut
#: there. Both cuts are named in the report.
MAX_FETCH_BYTES = 2_000_000
MAX_FETCH_CHARS = 20_000

#: One call's network patience, in seconds.
TIMEOUT_SECONDS = 15.0

_USER_AGENT = "MythicAgentCoder/1 (web knowledge tools; user-initiated)"

PLAIN_EXPLANATION = (
    "Web knowledge tools reach outside the machine only "
    "when you ask: /web search <query> sends that query "
    "text to the configured search endpoint (the shipped "
    "default is DuckDuckGo's keyless HTML road — no API "
    "key) and /web fetch <url> reads one http(s) page and "
    "returns its readable text. Every result is a numbered "
    "citation, and when a session is attached the sources "
    "are written into the session journal as a web_citation "
    "event, so what was consulted stays on the record. A "
    "page that cannot be read comes back as an honest "
    "error with its reason — never as invented content."
)

USAGE = "Usage: /web search <query...> | /web fetch <url>"

#: A transport takes a URL and returns
#: ``(status, content_type, body_bytes)``. Injectable so
#: the slice is provable over loopback with no real
#: network; the default transport is the only code here
#: that touches the network at all.
Transport = Callable[[str], Tuple[int, str, bytes]]


def enabled_from_config(config: Optional[Dict[str, Any]]) -> bool:
    """Web tools are on unless config says so."""
    if not config:
        return True
    return config.get("web_tools", True) is not False


def endpoint_from_config(config: Optional[Dict[str, Any]]) -> str:
    """The configured search endpoint template."""
    if not config:
        return DEFAULT_SEARCH_ENDPOINT
    return str(config.get("web_search_endpoint")
               or DEFAULT_SEARCH_ENDPOINT)


def _default_transport(url: str) -> Tuple[int, str, bytes]:
    """The real network road: one GET via httpx2/httpx."""
    try:
        import httpx2
    except ImportError:  # pragma: no cover - declared fallback pattern
        import httpx as httpx2  # type: ignore[no-redef]
    with httpx2.Client(timeout=TIMEOUT_SECONDS,
                       follow_redirects=True) as client:
        response = client.get(url, headers={"User-Agent": _USER_AGENT})
    return (response.status_code,
            response.headers.get("content-type", ""),
            response.content)


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WebResult:
    """One search result — one numbered citation."""

    number: int
    title: str
    url: str
    snippet: str = ""

    def record(self) -> Dict[str, Any]:
        return {"number": self.number, "title": self.title,
                "url": self.url, "snippet": self.snippet}


@dataclass
class WebReport:
    """One web call's whole account."""

    kind: str = "search"  # search | fetch
    query: str = ""
    url: str = ""
    host: str = ""
    sent: str = ""
    status: str = "ok"  # ok | disabled | error
    results: List[WebResult] = field(default_factory=list)
    title: str = ""
    text: str = ""
    warnings: List[str] = field(default_factory=list)
    truncated: bool = False
    note: str = ""
    journaled: bool = False

    def record(self) -> Dict[str, Any]:
        return {"kind": self.kind, "query": self.query,
                "url": self.url, "host": self.host,
                "sent": self.sent, "status": self.status,
                "results": [r.record() for r in self.results],
                "citations": [r.record() for r in self.results],
                "title": self.title, "text": self.text,
                "warnings": list(self.warnings),
                "truncated": self.truncated,
                "note": self.note, "journaled": self.journaled}

    def citation_event(self) -> Dict[str, Any]:
        """The ``web_citation`` session-event payload."""
        event: Dict[str, Any] = {
            "type": "web_citation", "kind": self.kind,
            "host": self.host,
            "sources": [{"number": r.number, "title": r.title,
                         "url": r.url} for r in self.results],
        }
        if self.kind == "search":
            event["query"] = self.query
        else:
            event["url"] = self.url
            if self.title:
                event["title"] = self.title
        return event


# ---------------------------------------------------------------------------
# The search-results page parser (DuckDuckGo HTML shape, stdlib only)
# ---------------------------------------------------------------------------

def _unwrap_redirect(href: str) -> str:
    """Resolve a search engine's redirect wrapper to its target."""
    url = href.strip()
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    targets = params.get("uddg")
    if targets:
        return targets[0]
    return url


class _SearchPageParser(HTMLParser):
    """Collect (title, url, snippet) from a results page.

    The DuckDuckGo HTML shape: a result's title is an
    anchor carrying the ``result__a`` class; its snippet
    is the next element carrying ``result__snippet``.
    Anchors without that class are page furniture, not
    results.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: List[Dict[str, str]] = []
        self._current: Optional[Dict[str, str]] = None
        self._capture: Optional[str] = None
        self._chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]):
        classes = dict(attrs).get("class", "") or ""
        if tag == "a" and "result__a" in classes.split():
            href = dict(attrs).get("href", "") or ""
            self._current = {"title": "", "url": _unwrap_redirect(href),
                             "snippet": ""}
            self._capture = "title"
            self._chunks = []
        elif self._current is not None and \
                "result__snippet" in classes.split():
            self._capture = "snippet"
            self._chunks = []

    def handle_data(self, data: str):
        if self._capture:
            self._chunks.append(data)

    def handle_endtag(self, tag: str):
        if self._capture == "title" and tag == "a" and self._current:
            self._current["title"] = " ".join(
                "".join(self._chunks).split())
            self.results.append(self._current)
            self._capture = None
        elif self._capture == "snippet" and self._current is not None:
            self._current["snippet"] = " ".join(
                "".join(self._chunks).split())
            self._capture = None


def _parse_search_page(body: bytes) -> List[Dict[str, str]]:
    parser = _SearchPageParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    parser.close()
    return [r for r in parser.results if r["url"]]


# ---------------------------------------------------------------------------
# The fetched-page text extractor (stdlib only)
# ---------------------------------------------------------------------------

class _TextExtractor(HTMLParser):
    """A page's readable text: no scripts, no styles."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.chunks: List[str] = []
        self._hidden = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]):
        if tag in ("script", "style", "noscript"):
            self._hidden += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str):
        if tag in ("script", "style", "noscript") and self._hidden:
            self._hidden -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._in_title:
            self.title += data
        elif not self._hidden:
            text = " ".join(data.split())
            if text:
                self.chunks.append(text)


def _extract_text(content_type: str, body: bytes) -> Tuple[str, str]:
    """(title, readable text) for one fetched body."""
    if "html" in (content_type or "").lower():
        parser = _TextExtractor()
        parser.feed(body.decode("utf-8", errors="replace"))
        parser.close()
        return " ".join(parser.title.split()), "\n".join(parser.chunks)
    return "", body.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# The two tools
# ---------------------------------------------------------------------------

def _call(transport: Optional[Transport], url: str,
          report: WebReport) -> Optional[Tuple[str, bytes]]:
    """Run one transport call; on failure fill the error report."""
    road = transport or _default_transport
    try:
        status, content_type, body = road(url)
    except Exception as exc:
        report.status = "error"
        report.note = (f"the call to {report.host} failed before an "
                       f"answer came back: {exc} — nothing was read "
                       "and nothing is invented here")
        return None
    if status != 200:
        report.status = "error"
        report.note = (f"{report.host} answered with status {status}, "
                       "not 200 — nothing was read and nothing is "
                       "invented here")
        return None
    return content_type, body


def web_search(query: str, *, endpoint: str = DEFAULT_SEARCH_ENDPOINT,
               enabled: bool = True,
               transport: Optional[Transport] = None,
               max_results: int = MAX_RESULTS) -> WebReport:
    """Search the web once, through the configured endpoint.

    Raises :class:`ValueError` for an empty query or an
    endpoint template without ``{query}`` — refused
    before anything is sent. A failed call is an
    ``error`` report, never invented results.
    """
    if max_results <= 0:
        raise ValueError("max_results must be positive")
    text = (query or "").strip()
    report = WebReport(kind="search", query=text)
    if not enabled:
        report.status = "disabled"
        report.note = ("web tools are off (the web_tools setting), "
                       "so nothing was sent anywhere")
        return report
    if not text:
        raise ValueError(f"{USAGE} — a search needs its query")
    if "{query}" not in (endpoint or ""):
        raise ValueError(
            "the configured web_search_endpoint carries no {query} "
            "placeholder, so there is nowhere honest to put the "
            "query — the search was not sent")
    url = endpoint.replace("{query}", quote_plus(text))
    report.url = url
    report.host = urlparse(url).netloc
    report.sent = f"the query text {text!r}"
    got = _call(transport, url, report)
    if got is None:
        return report
    _, body = got
    found = _parse_search_page(body)
    if len(found) > max_results:
        report.truncated = True
        report.warnings.append(
            f"result cap reached ({max_results}); "
            f"{len(found) - max_results} further result(s) "
            "were not shown")
        found = found[:max_results]
    report.results = [
        WebResult(number=i + 1, title=r["title"], url=r["url"],
                  snippet=r["snippet"])
        for i, r in enumerate(found)]
    if not report.results:
        report.note = ("the search answered with no results — "
                       "that is the answer, not an error")
    return report


def web_fetch(url: str, *, enabled: bool = True,
              transport: Optional[Transport] = None,
              max_bytes: int = MAX_FETCH_BYTES,
              max_chars: int = MAX_FETCH_CHARS) -> WebReport:
    """Fetch one http(s) page and return its readable text.

    Raises :class:`ValueError` for a non-http(s) URL —
    refused before anything is sent. A failed call is
    an ``error`` report, never invented content.
    """
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    target = (url or "").strip()
    report = WebReport(kind="fetch", url=target)
    if not enabled:
        report.status = "disabled"
        report.note = ("web tools are off (the web_tools setting), "
                       "so nothing was sent anywhere")
        return report
    parsed = urlparse(target)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"web fetch reads http(s) pages only — {target!r} was "
            "refused and nothing was sent")
    report.host = parsed.netloc
    report.sent = f"a request for the page {target}"
    got = _call(transport, target, report)
    if got is None:
        return report
    content_type, body = got
    if len(body) > max_bytes:
        report.truncated = True
        report.warnings.append(
            f"page body cap reached ({max_bytes} bytes); the rest "
            "of the page was not read")
        body = body[:max_bytes]
    title, text = _extract_text(content_type, body)
    report.title = title
    if len(text) > max_chars:
        report.truncated = True
        report.warnings.append(
            f"text cap reached ({max_chars} characters); the rest "
            "of the text was not shown")
        text = text[:max_chars]
    report.text = text
    if not text:
        report.note = ("the page answered with no readable text — "
                       "that is the answer, not an error")
    if report.title:
        report.results = [WebResult(number=1, title=report.title,
                                    url=target)]
    return report


# ---------------------------------------------------------------------------
# Surfaces: the shared parser + formatters
# ---------------------------------------------------------------------------

def parse_web_args(arguments: str) -> Dict[str, Any]:
    """Parse ``/web`` arguments into a web request.

    Grammar::

        /web search <query...>
        /web fetch <url>

    Raises :class:`ValueError` on a usage error.
    """
    text = (arguments or "").strip()
    if not text:
        raise ValueError(USAGE)
    tokens = text.split(None, 1)
    head = tokens[0].lower()
    rest = tokens[1].strip() if len(tokens) > 1 else ""
    if head == "search":
        if not rest:
            raise ValueError(f"{USAGE} — a search needs its query")
        return {"action": "search", "query": rest}
    if head == "fetch":
        if not rest:
            raise ValueError(f"{USAGE} — a fetch needs its URL")
        return {"action": "fetch", "url": rest}
    raise ValueError(f"{USAGE} — the roads are search and fetch")


def format_web_report(status: Dict[str, Any]) -> str:
    """One web call's account, from an Agent web-status mapping."""
    report = status["report"]
    if report["kind"] == "search":
        lines = [
            f"Web search ({WEB_SLICE}): {len(report['results'])} "
            f"result(s) for {report['query']!r} from "
            f"{report['host']} (sent: {report['sent']})."]
        for result in report["results"]:
            lines.append(f"  [{result['number']}] {result['title']}")
            lines.append(f"      {result['url']}")
            if result["snippet"]:
                lines.append(f"      {result['snippet']}")
    else:
        lines = [
            f"Web fetch ({WEB_SLICE}): {report['url']} from "
            f"{report['host']} (sent: {report['sent']})."]
        if report["title"]:
            lines.append(f"  Title: {report['title']}")
        if report["text"]:
            lines.append(report["text"])
    if report["note"]:
        lines.append(f"  {report['note']}")
    for warning in report["warnings"]:
        lines.append(f"  Warning: {warning}")
    if report["journaled"]:
        lines.append("  Sources cited into the session journal "
                     "(web_citation).")
    lines.append(status["plain_explanation"])
    return "\n".join(lines)


def render_markdown(report: WebReport) -> str:
    """Render *report* as a human report, from its own record."""
    data = report.record()
    lines = [
        "# Web Knowledge — search and fetch",
        "",
        f"*Slice {WEB_SLICE} of the All-Features road "
        "(Part III — Code Intelligence).*",
        "",
    ]
    if data["kind"] == "search":
        lines.append(
            f"**Search** for `{data['query']}` via {data['host']}: "
            f"{len(data['results'])} result(s).")
        lines += ["", "## Citations", ""]
        if data["citations"]:
            for cite in data["citations"]:
                lines.append(
                    f"- [{cite['number']}] [{cite['title']}]"
                    f"({cite['url']})"
                    + (f" — {cite['snippet']}" if cite["snippet"]
                       else ""))
        else:
            lines.append("- none")
    else:
        lines.append(
            f"**Fetch** of {data['url']} via {data['host']}.")
        if data["title"]:
            lines += ["", f"## {data['title']}"]
        lines += ["", data["text"] or "(no readable text)"]
    if data["warnings"]:
        lines += ["", "## Warnings", ""]
        for warning in data["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
