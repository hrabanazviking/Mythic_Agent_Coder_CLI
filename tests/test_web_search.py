"""M-059 — Web knowledge tools.

TIER: integration

Web search and fetch as first-class tools, proven with
no real network: the module's transport is injected, and
the live proof runs over a loopback HTTP server serving
a DuckDuckGo-shaped results page and one article page.
Search results are numbered citations with redirect
wrappers unwrapped; fetch returns readable text with
scripts dropped; failures are honest error reports,
never invented content; the Agent cites sources into
the session journal as a web_citation event; and a
switched-off road sends nothing at all.
"""

from __future__ import annotations

import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mythic_agent.tools import web_search as ws
from mythic_agent.tools.web_search import (
    DEFAULT_SEARCH_ENDPOINT, WEB_SLICE, enabled_from_config,
    endpoint_from_config, format_web_report, parse_web_args,
    render_markdown, web_fetch, web_search,
)

RESULTS_PAGE = """<!DOCTYPE html>
<html><head><title>python changelog - DuckDuckGo</title></head>
<body>
<a class="header" href="/">not a result</a>
<div class="result">
  <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fdocs.python.org%2F3%2Fwhatsnew%2F&amp;rut=abc">What&#x27;s New In Python</a>
  <a class="result__snippet" href="//duckduckgo.com/l/?uddg=x">The changelog for the latest release.</a>
</div>
<div class="result">
  <a class="result__a" href="https://example.org/errors">Common Errors</a>
  <td class="result__snippet">Fix your traceback fast.</td>
</div>
</body></html>
""".encode("utf-8")

ARTICLE_PAGE = """<!DOCTYPE html>
<html><head><title>The Answer Page</title>
<script>var secret = "do not show";</script>
<style>.x { color: red; }</style></head>
<body><h1>Heading One</h1><p>First paragraph of wisdom.</p>
<p>Second paragraph.</p></body></html>
""".encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - the server's own spelling
        if self.path.startswith("/search"):
            body, kind = RESULTS_PAGE, "text/html"
        elif self.path.startswith("/article"):
            body, kind = ARTICLE_PAGE, "text/html"
        elif self.path.startswith("/plain"):
            body, kind = b"plain text body", "text/plain"
        elif self.path.startswith("/broken"):
            self.send_response(500)
            self.end_headers()
            return
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the test run quiet
        pass


@pytest.fixture()
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def _counting_transport(calls, reply=(200, "text/html", RESULTS_PAGE)):
    def transport(url):
        calls.append(url)
        return reply
    return transport


# ---------------------------------------------------------------- basics

def test_slice_config_and_endpoint():
    assert WEB_SLICE == "M-059"
    assert enabled_from_config(None) is True
    assert enabled_from_config({}) is True
    assert enabled_from_config({"web_tools": False}) is False
    assert endpoint_from_config(None) == DEFAULT_SEARCH_ENDPOINT
    assert "{query}" in DEFAULT_SEARCH_ENDPOINT
    assert endpoint_from_config(
        {"web_search_endpoint": "http://x.test/?q={query}"}
    ) == "http://x.test/?q={query}"


def test_disabled_road_sends_nothing():
    calls = []
    report = web_search("anything", enabled=False,
                        transport=_counting_transport(calls))
    assert report.status == "disabled"
    assert report.results == []
    assert calls == []
    report = web_fetch("https://example.org/", enabled=False,
                       transport=_counting_transport(calls))
    assert report.status == "disabled"
    assert calls == []


def test_usage_errors_raise_before_anything_is_sent():
    calls = []
    transport = _counting_transport(calls)
    with pytest.raises(ValueError):
        web_search("   ", transport=transport)
    with pytest.raises(ValueError):
        web_search("q", endpoint="https://x.test/no-placeholder",
                   transport=transport)
    with pytest.raises(ValueError):
        web_fetch("file:///etc/passwd", transport=transport)
    with pytest.raises(ValueError):
        web_fetch("ftp://example.org/x", transport=transport)
    with pytest.raises(ValueError):
        web_fetch("not a url", transport=transport)
    assert calls == []


# ---------------------------------------------------------------- search

def test_search_parses_results_and_unwraps_redirects(server):
    report = web_search(
        "python changelog",
        endpoint=server + "/search?q={query}")
    assert report.status == "ok"
    assert report.host.startswith("127.0.0.1")
    assert "python changelog" in report.sent
    assert [r.number for r in report.results] == [1, 2]
    first, second = report.results
    assert first.title == "What's New In Python"
    assert first.url == "https://docs.python.org/3/whatsnew/"
    assert first.snippet == "The changelog for the latest release."
    assert second.url == "https://example.org/errors"
    assert second.snippet == "Fix your traceback fast."
    record = report.record()
    assert record["citations"][0]["url"] == first.url


def test_search_query_is_url_encoded(server):
    seen = []

    def transport(url):
        seen.append(url)
        return 200, "text/html", RESULTS_PAGE

    web_search("a+b & c?", endpoint=server + "/search?q={query}",
               transport=transport)
    assert seen and "a%2Bb+%26+c%3F" in seen[0]


def test_search_result_cap_truncates_and_says_so():
    report = web_search("q", transport=_counting_transport([]),
                        max_results=1)
    assert len(report.results) == 1
    assert report.truncated is True
    assert any("result cap reached" in w for w in report.warnings)


def test_search_http_error_is_a_report_never_invented(server):
    report = web_search("q", endpoint=server + "/broken?q={query}")
    assert report.status == "error"
    assert report.results == []
    assert "500" in report.note


def test_search_transport_failure_is_a_report():
    def boom(url):
        raise OSError("no route to host")

    report = web_search("q", transport=boom)
    assert report.status == "error"
    assert report.results == []
    assert "no route to host" in report.note


def test_search_no_results_is_an_answer():
    report = web_search(
        "q", transport=_counting_transport(
            [], reply=(200, "text/html", b"<html><body></body></html>")))
    assert report.status == "ok"
    assert report.results == []
    assert "no results" in report.note


# ---------------------------------------------------------------- fetch

def test_fetch_extracts_readable_text(server):
    report = web_fetch(server + "/article")
    assert report.status == "ok"
    assert report.title == "The Answer Page"
    assert "Heading One" in report.text
    assert "First paragraph of wisdom." in report.text
    assert "do not show" not in report.text
    assert "color: red" not in report.text
    assert report.results[0].url == server + "/article"


def test_fetch_plain_text_passes_through(server):
    report = web_fetch(server + "/plain")
    assert report.status == "ok"
    assert report.text == "plain text body"


def test_fetch_caps_name_themselves(server):
    report = web_fetch(server + "/article", max_chars=10)
    assert report.truncated is True
    assert len(report.text) == 10
    assert any("text cap reached" in w for w in report.warnings)
    report = web_fetch(server + "/article", max_bytes=64)
    assert report.truncated is True
    assert any("page body cap reached" in w for w in report.warnings)


def test_fetch_http_error_is_a_report(server):
    report = web_fetch(server + "/broken")
    assert report.status == "error"
    assert report.text == ""
    assert "500" in report.note


# ---------------------------------------------------------------- citations

def test_citation_event_carries_the_sources(server):
    report = web_search("python changelog",
                        endpoint=server + "/search?q={query}")
    event = report.citation_event()
    assert event["type"] == "web_citation"
    assert event["kind"] == "search"
    assert event["query"] == "python changelog"
    assert event["sources"][0] == {
        "number": 1, "title": "What's New In Python",
        "url": "https://docs.python.org/3/whatsnew/"}
    fetched = web_fetch(server + "/article")
    event = fetched.citation_event()
    assert event["kind"] == "fetch"
    assert event["url"] == server + "/article"
    assert event["title"] == "The Answer Page"


# ---------------------------------------------------------------- surfaces

def test_parse_args_roads_and_usage_errors():
    assert parse_web_args("search python docs") == {
        "action": "search", "query": "python docs"}
    assert parse_web_args("fetch https://example.org/x") == {
        "action": "fetch", "url": "https://example.org/x"}
    for bad in ("", "search", "fetch", "browse x"):
        with pytest.raises(ValueError):
            parse_web_args(bad)


def test_format_and_render_carry_citations(server):
    report = web_search("python changelog",
                        endpoint=server + "/search?q={query}")
    status = {"report": report.record(),
              "plain_explanation": ws.PLAIN_EXPLANATION}
    text = format_web_report(status)
    assert "Web search (M-059)" in text
    assert "[1] What's New In Python" in text
    assert "https://docs.python.org/3/whatsnew/" in text
    markdown = render_markdown(report)
    assert "[1]" in markdown and "docs.python.org" in markdown


def test_agent_journals_citations_when_a_session_is_attached(server):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = Path(".")
    agent.config = {"web_search_endpoint": server + "/search?q={query}"}
    agent._session_store = object()
    agent.session_id = "s-test"
    events = []
    agent._checkpoint = lambda event=None, **kw: events.append(event)
    status = agent.web_search("python changelog")
    assert status["report"]["journaled"] is True
    assert events and events[0]["type"] == "web_citation"
    assert events[0]["sources"][0]["url"] == \
        "https://docs.python.org/3/whatsnew/"
    status = agent.web_fetch(server + "/article")
    assert status["report"]["title"] == "The Answer Page"
    assert events[-1]["kind"] == "fetch"


def test_agent_without_a_session_journals_nothing(server):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = Path(".")
    agent.config = {"web_search_endpoint": server + "/search?q={query}"}
    agent._session_store = None
    agent.session_id = None
    status = agent.web_search("python changelog")
    assert status["report"]["journaled"] is False
    assert status["report"]["results"]


def test_agent_respects_the_config_switch(server):
    from mythic_agent.agents.llm import Agent

    agent = Agent.__new__(Agent)
    agent.project_root = Path(".")
    agent.config = {"web_tools": False,
                    "web_search_endpoint": server + "/search?q={query}"}
    agent._session_store = None
    agent.session_id = None
    status = agent.web_search("python changelog")
    assert status["report"]["status"] == "disabled"
    assert status["report"]["results"] == []


def test_terminal_road(server):
    from mythic_agent.agents.llm import Agent
    from mythic_agent.terminal import _slash

    agent = Agent.__new__(Agent)
    agent.project_root = Path(".")
    agent.config = {"web_search_endpoint": server + "/search?q={query}"}
    agent._session_store = None
    agent.session_id = None
    handled, _, text = _slash(agent, "/web search python changelog")
    assert handled and "Web search (M-059)" in text
    assert "[1]" in text
    handled, _, text = _slash(agent, "/web fetch " + server + "/article")
    assert handled and "The Answer Page" in text
    handled, _, text = _slash(agent, "/web fetch file:///etc/passwd")
    assert handled and "refused" in text
    handled, _, text = _slash(agent, "/web")
    assert handled and "Usage" in text
