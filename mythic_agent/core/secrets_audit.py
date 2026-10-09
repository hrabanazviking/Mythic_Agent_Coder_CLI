"""Scan text for credential patterns and report findings.

Used by redaction (to mask secrets in logs, transcripts and exports) and by
security audits of tool inputs/outputs. Findings never carry the raw secret,
only a masked preview, so audit reports are safe to store and display.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SecretFinding:
    """One detected credential-like span."""

    kind: str
    start: int
    end: int
    preview: str  # masked preview, e.g. "sk-...9f2a" -- never the raw secret


# (kind, compiled pattern, group holding the secret; 0 = whole match)
_PATTERNS: list[tuple[str, re.Pattern[str], int]] = [
    ("openai_key", re.compile(r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_-]{20,}"), 0),
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), 0),
    (
        "github_token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}"),
        0,
    ),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0),
    (
        "aws_secret_key",
        re.compile(r"(?i)\baws[\w.\-]{0,40}?secret\b.{0,10}?['\"]?\s*[:=]\s*['\"]?([0-9a-zA-Z/+]{40})\b"),
        1,
    ),
    (
        "stripe_key",
        re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}"),
        0,
    ),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), 0),
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY(?: BLOCK)?-----"),
        0,
    ),
    (
        "bearer_token",
        re.compile(r"(?i)\bbearer\s+([A-Za-z0-9\-._~+/]{20,}={0,2})"),
        1,
    ),
    (
        "url_credentials",
        re.compile(r"(https?://)[^\s/@:/?#]+:[^\s/@?#]+@"),
        0,
    ),
    (
        "generic_secret",
        re.compile(
            r"(?i)\b(api[_-]?key|api[_-]?secret|secret[_-]?key|client[_-]?secret"
            r"|access[_-]?token|auth[_-]?token)\b\s*[:=]\s*['\"]?"
            r"([A-Za-z0-9_\-/+]{16,})['\"]?"
            r"(?![A-Za-z0-9_\-/+])"
        ),
        2,
    ),
]


def _masked_preview(secret: str) -> str:
    head = secret[:3]
    tail = secret[-4:] if len(secret) > 7 else ""
    return f"{head}...{tail}" if tail else f"{head}..."


def scan_secrets(text: str) -> list[SecretFinding]:
    """Return findings for every credential-like span in *text*.

    Overlapping matches are de-duplicated (the longest span wins); results
    are ordered by position.
    """
    if not isinstance(text, str) or not text:
        return []
    raw: list[SecretFinding] = []
    for kind, pattern, group in _PATTERNS:
        for match in pattern.finditer(text):
            secret = match.group(group)
            start, end = match.span(group)
            if not secret:
                continue
            raw.append(SecretFinding(kind, start, end, _masked_preview(secret)))
    # De-duplicate overlaps: sort by start, prefer the longest span.
    raw.sort(key=lambda f: (f.start, -(f.end - f.start)))
    findings: list[SecretFinding] = []
    for finding in raw:
        if findings and finding.start < findings[-1].end:
            continue  # overlapped by an earlier, longer-or-equal span
        findings.append(finding)
    return findings


def has_secrets(text: str) -> bool:
    """True when *text* contains anything credential-like."""
    return bool(scan_secrets(text))


def mask_text(text: str, mask: str = "[REDACTED]") -> str:
    """Replace every detected secret span with *mask*."""
    findings = scan_secrets(text)
    if not findings:
        return text
    parts: list[str] = []
    cursor = 0
    for finding in findings:
        parts.append(text[cursor : finding.start])
        parts.append(mask)
        cursor = finding.end
    parts.append(text[cursor:])
    return "".join(parts)


def count_by_kind(findings: list[SecretFinding]) -> dict[str, int]:
    """Tally findings by credential kind."""
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.kind] = counts.get(finding.kind, 0) + 1
    return counts


def audit_report(text: str) -> dict[str, object]:
    """Summarize a scan: total count, per-kind counts, masked previews.

    Safe to log or persist -- previews never contain raw secrets.
    """
    findings = scan_secrets(text)
    return {
        "findings": len(findings),
        "kinds": count_by_kind(findings),
        "previews": [
            {"kind": f.kind, "preview": f.preview, "position": f.start} for f in findings
        ],
    }


def scan_mapping(data: dict[str, object]) -> dict[str, list[SecretFinding]]:
    """Scan every string value in a flat mapping; key -> findings."""
    result: dict[str, list[SecretFinding]] = {}
    for key, value in data.items():
        if isinstance(value, str):
            findings = scan_secrets(value)
            if findings:
                result[str(key)] = findings
    return result
