"""Slice execution workflows for Mythic Engineering.

A *slice* is a unit of work defined by a :class:`SliceDefinition`: a name, a
description, an optional work-order path, and a list of acceptance-gate shell
commands.  :class:`SliceRunner` executes the gates sequentially, records the
results, and checkpoints progress to disk so an interrupted run can be resumed.
"""

from .slice_runner import (
    CheckpointError,
    GateResult,
    SliceDefinition,
    SliceResult,
    SliceRunner,
)

__all__ = [
    "CheckpointError",
    "GateResult",
    "SliceDefinition",
    "SliceResult",
    "SliceRunner",
]
