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
"""Tests for `flepimop2.job.abc.JobDryRun`."""

from flepimop2.job.abc import JobDryRun


def test_details_default_to_empty() -> None:
    """`details` defaults to an empty dict and is per-instance."""
    a = JobDryRun(command="a")
    b = JobDryRun(command="b")
    a.details["partition"] = "gpu"
    assert b.details == {}


def test_json_roundtrip() -> None:
    """A `JobDryRun` survives a JSON round-trip."""
    dry_run = JobDryRun(command="sbatch run.sh", details={"partition": "gpu"})
    restored = JobDryRun.model_validate_json(dry_run.model_dump_json())
    assert restored == dry_run
