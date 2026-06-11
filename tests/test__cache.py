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
"""Tests for the `flepimop2._cache` job-handle cache."""

from datetime import UTC, datetime
from pathlib import Path

from flepimop2 import _cache
from flepimop2.job.abc import JobHandle


def _handle(job_id: str, when: int = 0) -> JobHandle:
    """Build a fixed-timestamp handle whose ordering follows `when`.

    Args:
        job_id: The backend job identifier.
        when: Seconds offset applied to the submission timestamp, controlling
            relative ordering between handles.

    Returns:
        A `JobHandle` for the `shell` backend.
    """
    return JobHandle(
        job_id=job_id,
        backend="shell",
        submitted_at=datetime(2026, 1, 1, 0, 0, when, tzinfo=UTC),
    )


def test_save_and_load_job_roundtrips(tmp_path: Path) -> None:
    """A saved job should load back with its handle and config intact."""
    handle = _handle("42")
    config = {"module": "flepimop2.job.shell", "detach": False}

    _cache.save_job(handle, config, start=tmp_path)
    loaded = _cache.load_job("shell-42", start=tmp_path)

    assert loaded is not None
    assert loaded.handle == handle
    assert loaded.job_config == config


def test_load_job_by_bare_id_when_unambiguous(tmp_path: Path) -> None:
    """A bare job id should resolve when only one job has it."""
    _cache.save_job(_handle("7"), {"module": "shell"}, start=tmp_path)
    loaded = _cache.load_job("7", start=tmp_path)
    assert loaded is not None
    assert loaded.handle.job_id == "7"


def test_save_job_writes_handle_and_summary(tmp_path: Path) -> None:
    """Saving a job writes both its handle file and a summary entry."""
    _cache.save_job(_handle("1"), {"module": "shell"}, start=tmp_path)

    handle_file = tmp_path / ".flepimop2_cache/job/handles/shell-1.json"
    summary_file = tmp_path / ".flepimop2_cache/job/summary.json"
    assert handle_file.is_file()
    assert summary_file.is_file()

    summary = _cache.load_summary(start=tmp_path)
    assert [e.key for e in summary.jobs] == ["shell-1"]
    assert summary.jobs[0].status is None


def test_load_jobs_sorted_by_submission_time(tmp_path: Path) -> None:
    """Cached jobs are returned oldest-first regardless of save order."""
    _cache.save_job(_handle("late", when=30), {"module": "shell"}, start=tmp_path)
    _cache.save_job(_handle("early", when=10), {"module": "shell"}, start=tmp_path)

    ids = [c.handle.job_id for c in _cache.load_jobs(start=tmp_path)]
    assert ids == ["early", "late"]


def test_update_summary_status(tmp_path: Path) -> None:
    """Updating a summary status persists for later reads."""
    _cache.save_job(_handle("1"), {"module": "shell"}, start=tmp_path)
    _cache.update_summary_status("shell-1", "successful", start=tmp_path)

    summary = _cache.load_summary(start=tmp_path)
    assert summary.jobs[0].status == "successful"


def test_load_jobs_empty_when_no_cache(tmp_path: Path) -> None:
    """Loading from a directory without a cache yields no jobs."""
    assert _cache.load_jobs(start=tmp_path) == []
    assert _cache.load_job("shell-1", start=tmp_path) is None
    assert _cache.load_summary(start=tmp_path).jobs == []


def test_summary_serializes_as_bare_array(tmp_path: Path) -> None:
    """The root-model summary is persisted as a JSON array, not an object."""
    _cache.save_job(_handle("1"), {"module": "shell"}, start=tmp_path)

    raw = (tmp_path / ".flepimop2_cache/job/summary.json").read_text()
    assert raw.lstrip().startswith("[")

    summary = _cache.load_summary(start=tmp_path)
    assert len(summary) == 1
    assert [e.key for e in summary] == ["shell-1"]
