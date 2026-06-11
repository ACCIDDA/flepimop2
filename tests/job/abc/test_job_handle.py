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
"""Tests for `flepimop2.job.abc.JobHandle`."""

from datetime import UTC, datetime

import pytest

from flepimop2.job.abc import JobHandle


@pytest.fixture
def handle() -> JobHandle:
    """Return a fixed-timestamp JobHandle for use in format tests."""
    return JobHandle(
        job_id="42",
        backend="shell",
        submitted_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
    )


def test_str_format(handle: JobHandle) -> None:
    """str() should include the backend, job_id, and submission timestamp."""
    line = str(handle)
    assert "shell-42" in line
    assert "submitted_at=2026-01-15T12:00:00" in line


def test_str_is_single_line(handle: JobHandle) -> None:
    """str() must produce exactly one line (no embedded newlines)."""
    assert "\n" not in str(handle)


def test_metadata_defaults_to_empty_dict() -> None:
    """Metadata should default to an empty dict, not shared across instances."""
    h1 = JobHandle(
        job_id="1",
        backend="shell",
        submitted_at=datetime.now(tz=UTC),
    )
    h2 = JobHandle(
        job_id="2",
        backend="shell",
        submitted_at=datetime.now(tz=UTC),
    )
    h1.metadata["key"] = "value"
    assert "key" not in h2.metadata


def test_metadata_is_stored() -> None:
    """Metadata passed at construction time should be accessible."""
    h = JobHandle(
        job_id="99",
        backend="slurm",
        submitted_at=datetime.now(tz=UTC),
        metadata={"partition": "gpu", "account": "my-alloc"},
    )
    assert h.metadata["partition"] == "gpu"
    assert h.metadata["account"] == "my-alloc"
