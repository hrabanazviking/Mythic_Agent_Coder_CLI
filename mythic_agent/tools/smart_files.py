"""Smarter file operations for the Mythic agent.

Slice 18: fuzzy filename matching, project-aware search that respects
``.gitignore``, and unified-diff edit previews.
"""

import difflib
import fnmatch
from pathlib import Path

__all__ = [
    "fuzzy_score",
    "fuzzy_find",
    "load_gitignore",
    "respect_gitignore",
    "preview_edit",
]

#: Directories that are always skipped by fuzzy_find.
_ALWAYS_IGNORED = {".git", ".hg", ".svn", "__pycache__", ".mypy_cache",
                   ".pytest_cache", "node_modules", ".tox"}


def fuzzy_score(query: str, candidate: str) -> float:
    """Score how well *query* fuzzily matches *candidate*.

    A subsequence match over the candidate (case-insensitive). Contiguous
    matches and matches at word boundaries (start, after ``/``, ``-``,
    ``_``, ``.``) score higher. Returns 0.0 when the query is not a
    subsequence of the candidate; otherwise a value in ``(0, 1]``.
    """
    q = query.lower()
    c = candidate.lower()
    if not q:
        return 1.0
    if len(q) > len(c):
        return 0.0

    # Subsequence scan, preferring contiguous + boundary hits.
    score = 0.0
    last_index = -1
    contiguous = 0
    for ch in q:
        idx = c.find(ch, last_index + 1)
        if idx == -1:
            return 0.0
        boundary = idx == 0 or c[idx - 1] in "/-_. "
        if idx == last_index + 1:
            contiguous += 1
            score += 2.0 if boundary else 1.0
        else:
            contiguous = 0
            score += 0.5 if boundary else 0.1
        last_index = idx
    # Coverage bonus: shorter candidates that still match are preferred.
    coverage = len(q) / len(c)
    # Full-string exact match tops everything.
    if q == c:
        return 1.0
    return min(0.999, (score / (2.0 * len(q))) * 0.7 + coverage * 0.3)


def fuzzy_find(query: str, root: str | Path, *, limit: int = 20,
               respect_gitignore: bool = True) -> list[Path]:
    """Return up to *limit* paths under *root* best matching *query*.

    Matches against both the filename and the path relative to *root*.
    Always skips VCS/tooling directories; optionally also skips paths
    matching ``.gitignore`` rules at the root.
    """
    root = Path(root)
    patterns = load_gitignore(root) if respect_gitignore else []
    scored: list[tuple[float, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in _ALWAYS_IGNORED for part in rel.parts):
            continue
        if respect_gitignore and _ignored_by_gitignore(rel, patterns, path.is_dir()):
            continue
        name_score = fuzzy_score(query, path.name)
        rel_score = fuzzy_score(query, str(rel).replace("\\", "/"))
        best = max(name_score, rel_score)
        if best > 0.0:
            scored.append((best, path))
    scored.sort(key=lambda item: (-item[0], str(item[1])))
    return [path for _, path in scored[:limit]]


def load_gitignore(root: str | Path) -> list[str]:
    """Read ``.gitignore`` at *root* and return usable patterns."""
    gi = Path(root) / ".gitignore"
    patterns: list[str] = []
    if not gi.is_file():
        return patterns
    for line in gi.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def _ignored_by_gitignore(rel: Path, patterns: list[str], is_dir: bool) -> bool:
    """Apply .gitignore-style matching to a root-relative path."""
    rel_posix = rel.as_posix()
    ignored = False
    for raw in patterns:
        negated = raw.startswith("!")
        pat = raw[1:] if negated else raw
        dir_only = pat.endswith("/")
        if dir_only:
            pat = pat.rstrip("/")
        # fnmatch against the full relative path and against each path part.
        matched = (
            fnmatch.fnmatch(rel_posix, pat)
            or fnmatch.fnmatch(rel_posix, f"**/{pat}")
            or any(fnmatch.fnmatch(part, pat) for part in rel.parts)
        )
        if dir_only and not is_dir and matched:
            # A directory-only pattern still ignores the file if a parent
            # directory matched it.
            matched = any(
                fnmatch.fnmatch("/".join(rel.parts[: i + 1]), pat)
                or fnmatch.fnmatch("/".join(rel.parts[: i + 1]), f"**/{pat}")
                for i in range(len(rel.parts) - 1)
            )
        if matched:
            ignored = not negated
    return ignored


def respect_gitignore(paths: list[Path], root: str | Path) -> list[Path]:
    """Filter *paths*, dropping those that ``.gitignore`` at *root* excludes."""
    root = Path(root)
    patterns = load_gitignore(root)
    kept: list[Path] = []
    for path in paths:
        try:
            rel = Path(path).relative_to(root)
        except ValueError:
            # Path outside root: keep it (gitignore does not apply).
            kept.append(path)
            continue
        if not _ignored_by_gitignore(rel, patterns, Path(path).is_dir()):
            kept.append(path)
    return kept


def preview_edit(path: str | Path, old: str, new: str,
                 context: int = 3) -> str:
    """Render a unified diff of replacing *old* with *new* in *path*.

    Does not touch the file — it is a preview only.
    """
    try:
        current = Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        current = ""
    if old not in current:
        return f"--- no changes for {path} ---\n"
    new_content = current.replace(old, new, 1)
    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        n=context,
    )
    rendered = "".join(diff)
    if not rendered:
        return f"--- no changes for {path} ---\n"
    return rendered
