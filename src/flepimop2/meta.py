"""Metadata types for flepimop2 runs."""

__all__ = ["RunMeta"]

from datetime import datetime
from typing import Literal, NamedTuple


class RunMeta(NamedTuple):
    """
    Metadata for a flepimop2 run.

    Attributes:
        action: The action performed in the run (e.g., "simulate").
        timestamp: The timestamp when the run was executed.
        name: An optional name for the run, typically pulled from the config.
    """

    action: Literal["simulate"]
    timestamp: datetime
    name: str | None
