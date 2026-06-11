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
"""Tests for `flepimop2.job.abc.JobStatus` and `JobStatusResult`."""

from datetime import UTC, datetime

import pytest

from flepimop2.job.abc import JobHandle, JobStatus, JobStatusResult

_FINISHED_STATUSES = frozenset({
    JobStatus.SUCCESSFUL,
    JobStatus.FAILED,
    JobStatus.FINISHED_UNKNOWN,
})


@pytest.mark.parametrize("status", list(JobStatus))
def test_is_finished(status: JobStatus) -> None:
    """Terminal statuses report `is_finished`; in-flight ones do not."""
    assert status.is_finished is (status in _FINISHED_STATUSES)


def test_status_result_is_a_handle() -> None:
    """A `JobStatusResult` carries all handle fields plus a status."""
    result = JobStatusResult(
        job_id="42",
        backend="shell",
        submitted_at=datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC),
        status=JobStatus.RUNNING,
    )
    assert isinstance(result, JobHandle)
    assert result.status is JobStatus.RUNNING
    assert "status=running" in str(result)


def test_status_result_json_roundtrip() -> None:
    """A `JobStatusResult` survives a JSON round-trip (for caching)."""
    result = JobStatusResult(
        job_id="1",
        backend="shell",
        status=JobStatus.SUCCESSFUL,
        detail={"returncode": 0},
    )
    restored = JobStatusResult.model_validate_json(result.model_dump_json())
    assert restored == result
