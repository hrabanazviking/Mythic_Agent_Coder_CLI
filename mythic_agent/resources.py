"""Locate immutable resources in installed wheels and editable checkouts."""

__all__ = [
    "Path",
    "character_directory",
    "engineering_protocol",
    "files",
]

from importlib.resources import files
from pathlib import Path


def character_directory() -> Path:
    """Return the character asset directory independently of working directory."""
    packaged = files("mythic_agent").joinpath("resources", "characters")
    if packaged.is_dir():
        return Path(str(packaged))
    return Path(__file__).resolve().parent.parent / "default_agent_characters"


def engineering_protocol() -> str:
    """Read the shipped Mythic Engineering protocol."""
    packaged = files("mythic_agent").joinpath("resources", "engineering.md")
    if packaged.is_file():
        return packaged.read_text(encoding="utf-8")
    source = Path(__file__).resolve().parent.parent / "Mythic-Engineering"
    return (source / "Mythic-Engineering_SKILL.md").read_text(encoding="utf-8")
