"""Prevent GitHub Desktop checkout failures from Windows-invalid tracked paths."""

import subprocess
from pathlib import Path


def test_tracked_paths_are_valid_on_windows():
    root = Path(__file__).resolve().parents[1]
    paths = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root,
    ).decode("utf-8").split("\x00")
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10))
    invalid = []
    for path in filter(None, paths):
        for part in path.split("/"):
            if (
                any(character in '<>:"\\|?*' or ord(character) < 32 for character in part)
                or part.endswith((" ", "."))
                or part.split(".")[0].upper() in reserved
            ):
                invalid.append(path)
                break
    assert not invalid, f"Windows cannot check out these tracked paths: {invalid}"
