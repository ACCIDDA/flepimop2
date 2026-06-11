# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Persistent on-disk cache for flepimop2, e.g. submitted job handles.

The cache lives in a `.flepimop2_cache/` directory rooted at the current
working directory and is namespaced by general task. For job tracking the
layout is::

    .flepimop2_cache/
      job/
        handles/
          <backend>-<job_id>.json   # one cached job per file
        summary.json                # rollup for quick listing

All contents are JSON, (de)serialized via `pydantic` so we get validation for
free. Only the resolved job module's configuration is cached alongside each
handle, which is enough to rebuild the exact `JobABC` instance that launched
the job when later checking its status.
"""

__all__ = [
    "CachedJob",
    "JobCacheSummary",
    "JobSummaryEntry",
    "load_job",
    "load_jobs",
    "load_summary",
    "save_job",
    "update_summary_status",
]

import re
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, Field, RootModel

from flepimop2.job.abc import JobHandle

_CACHE_DIRNAME: Final[str] = ".flepimop2_cache"
_JOB_NAMESPACE: Final[str] = "job"
_NONWORD: Final[re.Pattern[str]] = re.compile(r"[^A-Za-z0-9._-]+")


def _cache_root(start: Path | None = None) -> Path:
    """Return the root `.flepimop2_cache` directory.

    The returned path is not guaranteed to exist; it is created lazily by the
    functions that write into it.

    Args:
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The path to the cache root (not necessarily created yet).

    Examples:
        >>> from pathlib import Path
        >>> from flepimop2._cache import _cache_root
        >>> _cache_root(Path("/tmp/project"))
        PosixPath('/tmp/project/.flepimop2_cache')
    """
    base = Path.cwd() if start is None else start
    return base / _CACHE_DIRNAME


def _job_handles_dir(start: Path | None = None) -> Path:
    """Return the directory holding cached individual job handle files.

    Args:
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The path to the `job/handles` directory (not necessarily created yet).

    Examples:
        >>> from pathlib import Path
        >>> from flepimop2._cache import _job_handles_dir
        >>> _job_handles_dir(Path("/tmp/project"))
        PosixPath('/tmp/project/.flepimop2_cache/job/handles')
    """
    return _cache_root(start) / _JOB_NAMESPACE / "handles"


def _summary_path(start: Path | None = None) -> Path:
    """Return the path to the job cache summary file.

    Args:
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The path to `job/summary.json` (not necessarily created yet).

    Examples:
        >>> from pathlib import Path
        >>> from flepimop2._cache import _summary_path
        >>> _summary_path(Path("/tmp/project"))
        PosixPath('/tmp/project/.flepimop2_cache/job/summary.json')
    """
    return _cache_root(start) / _JOB_NAMESPACE / "summary.json"


def _job_key(handle: JobHandle) -> str:
    """Build a stable, filesystem-safe key for a job handle.

    The key is `<backend>-<job_id>` with any character outside
    `[A-Za-z0-9._-]` collapsed to a single underscore, so it is safe to use as
    a file name.

    Args:
        handle: The job handle to derive a key from.

    Returns:
        A `<backend>-<job_id>` key with unsafe characters replaced.

    Examples:
        >>> from flepimop2.job.abc import JobHandle
        >>> from flepimop2._cache import _job_key
        >>> _job_key(JobHandle(job_id="42", backend="shell"))
        'shell-42'
        >>> _job_key(JobHandle(job_id="1/2 3", backend="slurm"))
        'slurm-1_2_3'
    """
    raw = f"{handle.backend}-{handle.job_id}"
    return _NONWORD.sub("_", raw)


class CachedJob(BaseModel):
    """A submitted job handle plus the config needed to recreate its backend.

    Attributes:
        key: Stable, filesystem-safe identifier for this cached job.
        handle: The handle returned when the job was submitted.
        job_config: The resolved job module configuration (a `model_dump()` of
            the `JobABC` instance) sufficient to rebuild the exact backend via
            `flepimop2.job.abc.build`.
    """

    key: str
    handle: JobHandle
    job_config: dict[str, Any]


class JobSummaryEntry(BaseModel):
    """A lightweight summary of a cached job for quick listing.

    Attributes:
        key: Stable identifier matching the corresponding `CachedJob`.
        backend: The job module name that produced the handle.
        job_id: The backend job identifier.
        submitted_at: When the job was submitted.
        status: The last-known lifecycle status, if it has been refreshed.
    """

    key: str
    backend: str
    job_id: str
    submitted_at: datetime
    status: str | None = None


class JobCacheSummary(RootModel[list[JobSummaryEntry]]):
    """A rollup of all cached jobs, persisted as `job/summary.json`.

    Modeled as a `pydantic` root model whose root is the list of summary
    entries, so the on-disk JSON is a bare array rather than an object wrapping
    a `jobs` key. The list is exposed via `jobs` and the usual sequence
    protocols.
    """

    root: list[JobSummaryEntry] = Field(default_factory=list)

    @property
    def jobs(self) -> list[JobSummaryEntry]:
        """The summary entries, keyed implicitly by their `key` field."""
        return self.root

    def __iter__(self) -> Iterator[JobSummaryEntry]:  # type: ignore[override]
        """Iterate over the summary entries.

        Returns:
            An iterator over the summary entries.
        """
        return iter(self.root)

    def __len__(self) -> int:
        """Return the number of summary entries."""
        return len(self.root)


def _read_summary(start: Path | None = None) -> JobCacheSummary:
    """Read the job cache summary, returning an empty summary if absent.

    Args:
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The parsed summary, or an empty `JobCacheSummary` if none exists.
    """
    path = _summary_path(start)
    if not path.is_file():
        return JobCacheSummary()
    return JobCacheSummary.model_validate_json(path.read_text())


def _write_summary(summary: JobCacheSummary, start: Path | None = None) -> None:
    """Write the job cache summary, creating parent directories as needed.

    Args:
        summary: The summary to serialize to `job/summary.json`.
        start: The directory to root the cache in. Defaults to the current
            working directory.
    """
    path = _summary_path(start)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summary.model_dump_json(indent=2))


def save_job(
    handle: JobHandle,
    job_config: dict[str, Any],
    *,
    start: Path | None = None,
) -> CachedJob:
    """Persist a submitted job handle and its backend configuration.

    Writes an individual handle file under `job/handles/` and refreshes the
    matching entry in `job/summary.json`.

    Args:
        handle: The handle returned when the job was submitted.
        job_config: The resolved job module configuration, as produced by
            `JobABC.model_dump()`.
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The `CachedJob` that was written.
    """
    key = _job_key(handle)
    cached = CachedJob(key=key, handle=handle, job_config=job_config)

    handles_dir = _job_handles_dir(start)
    handles_dir.mkdir(parents=True, exist_ok=True)
    (handles_dir / f"{key}.json").write_text(cached.model_dump_json(indent=2))

    summary = _read_summary(start)
    entry = JobSummaryEntry(
        key=key,
        backend=handle.backend,
        job_id=handle.job_id,
        submitted_at=handle.submitted_at,
    )
    summary.root = [j for j in summary.root if j.key != key]
    summary.root.append(entry)
    _write_summary(summary, start)

    return cached


def load_summary(start: Path | None = None) -> JobCacheSummary:
    """Load the job cache summary.

    The summary is a lightweight rollup of all cached jobs (including each
    job's last-known status) that callers can scan without reading every
    individual handle file.

    Args:
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The summary, or an empty summary if the cache does not yet exist. Entries
        are sorted by submission time (oldest first).
    """
    summary = _read_summary(start)
    summary.root.sort(key=lambda e: e.submitted_at)
    return summary


def load_jobs(start: Path | None = None) -> list[CachedJob]:
    """Load every cached job, sorted by submission time (oldest first).

    Args:
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The cached jobs. Empty if the cache does not yet exist.
    """
    handles_dir = _job_handles_dir(start)
    if not handles_dir.is_dir():
        return []
    jobs = [
        CachedJob.model_validate_json(path.read_text())
        for path in sorted(handles_dir.glob("*.json"))
    ]
    return sorted(jobs, key=lambda c: c.handle.submitted_at)


def load_job(key: str, start: Path | None = None) -> CachedJob | None:
    """Load a single cached job by key.

    Args:
        key: The `<backend>-<job_id>` key (as stored). A bare `job_id` is also
            accepted and matched when unambiguous.
        start: The directory to root the cache in. Defaults to the current
            working directory.

    Returns:
        The matching `CachedJob`, or `None` if no unambiguous match exists.
    """
    handles_dir = _job_handles_dir(start)
    if not handles_dir.is_dir():
        return None

    exact = handles_dir / f"{_NONWORD.sub('_', key)}.json"
    if exact.is_file():
        return CachedJob.model_validate_json(exact.read_text())

    matches = [c for c in load_jobs(start) if c.handle.job_id == key]
    if len(matches) == 1:
        return matches[0]
    return None


def update_summary_status(
    key: str,
    status: str,
    *,
    start: Path | None = None,
) -> None:
    """Patch the last-known status of a cached job in the summary file.

    Args:
        key: The cached job key to update.
        status: The new last-known status string.
        start: The directory to root the cache in. Defaults to the current
            working directory.
    """
    summary = _read_summary(start)
    changed = False
    for entry in summary.jobs:
        if entry.key == key:
            entry.status = status
            changed = True
    if changed:
        _write_summary(summary, start)
