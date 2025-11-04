"""Metadata types for flepimop2 runs."""

__all__ = ["RunMeta"]

from datetime import UTC, datetime
from typing import Literal, NamedTuple


class RunMeta(NamedTuple):
    """
    Metadata for a flepimop2 run.

    Attributes:
        action: The action performed in the run (e.g., "simulate").
        timestamp: The timestamp when the run was executed. Defaults to current UTC
            time.
        name: An optional name for the run, typically pulled from the config.

    Examples:
        >>> from flepimop2.meta import RunMeta
        >>> run_meta = RunMeta(name="test_run")
        >>> run_meta.action
        'simulate'
        >>> run_meta.timestamp
        datetime.datetime(..., tzinfo=datetime.timezone.utc)
        >>> run_meta.name
        'test_run'
    """

    action: Literal["simulate"] = "simulate"
    timestamp: datetime = datetime.now(UTC)
    name: str | None = None
