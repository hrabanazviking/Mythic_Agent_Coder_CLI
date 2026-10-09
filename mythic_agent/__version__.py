"""Single source of truth for the Mythic Agent package version.

Keep this module import-light: it is read by the build backend
(hatchling ``[tool.hatch.version]``) and imported at runtime by
``mythic_agent.cli`` for ``mythic --version`` without starting workers.
Do not add imports or side effects here.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
