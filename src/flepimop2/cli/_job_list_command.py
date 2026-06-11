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
"""The `flepimop2 job list` command."""

__all__ = []

from typing import Any

import click

from flepimop2 import _cache
from flepimop2.cli._cli_command import CliCommand
from flepimop2.job.abc import JobStatus
from flepimop2.job.abc import build as build_job
from flepimop2.typing import ExitCode


class JobListCommand(CliCommand):
    """
    List submitted jobs and their current status.

    Reads jobs cached under `.flepimop2_cache/job/` (recorded when they were
    submitted via `flepimop2 job <subcommand>`) and prints a line per job.
    Finished jobs are retained, so this is also a record of recently completed
    work.

    To stay fast, the command only re-queries the backend for jobs whose
    last-known status (read from `summary.json`) was unfinished - i.e. never
    checked, pending, or running. Jobs already known to be finished are reported
    from the cached summary without contacting the backend again.
    """

    def run(self, **kwargs: Any) -> ExitCode:
        """
        List cached jobs, refreshing only those not yet known to be finished.

        Returns:
            An exit code indicating success.
        """
        del kwargs
        summary = _cache.load_summary()
        if not summary.jobs:
            click.echo("No jobs found.")
            return ExitCode.OKAY

        for entry in summary.jobs:
            last_known = self._parse_status(entry.status)
            if last_known is not None and last_known.is_finished:
                click.echo(
                    f"{entry.backend}-{entry.job_id} "
                    f"submitted_at={entry.submitted_at:%Y-%m-%dT%H:%M:%S} "
                    f"status={last_known.value}"
                )
                continue
            self._refresh_and_echo(entry.key)
        return ExitCode.OKAY

    def _refresh_and_echo(self, key: str) -> None:
        """Re-query one cached job from its backend and print its status."""
        cached = _cache.load_job(key)
        if cached is None:
            self.warning("Cached job '%s' is missing its handle file.", key)
            return
        try:
            job = build_job(cached.job_config)
            result = job.status(cached.handle)
            _cache.update_summary_status(cached.key, result.status.value)
            click.echo(str(result))
        except Exception as exc:  # noqa: BLE001
            self.warning("Could not refresh job '%s': %s", key, exc)
            click.echo(f"{cached.handle} status=unknown")

    @staticmethod
    def _parse_status(value: str | None) -> JobStatus | None:
        """Parse a summary status string into a `JobStatus`, if recognized.

        Args:
            value: The stored status string, or `None` if never refreshed.

        Returns:
            The matching `JobStatus`, or `None` if absent or unrecognized.
        """
        if value is None:
            return None
        try:
            return JobStatus(value)
        except ValueError:
            return None

    @classmethod
    def command_name(cls) -> str:
        """Return the command name used within the `job` group."""
        return "list"
