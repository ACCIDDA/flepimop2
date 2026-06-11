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
"""The `flepimop2 job status` command."""

__all__ = []

import click
from typing_extensions import override

from flepimop2 import _cache
from flepimop2.cli._cli_command import CliCommand
from flepimop2.job.abc import build as build_job
from flepimop2.typing import ExitCode


class JobStatusCommand(CliCommand):
    """
    Show the status of a single submitted job.

    Looks up a job cached under `.flepimop2_cache/job/` by its identifier,
    rebuilds the exact job backend that launched it from the cached
    configuration, queries the backend, and prints the job's current status
    along with any backend-specific detail.
    """

    @override
    def run(  # type: ignore[override]
        self, *, job_id: str, **kwargs: object
    ) -> ExitCode:
        """
        Report the status of the cached job identified by `job_id`.

        Args:
            job_id: The `<backend>-<job_id>` key or bare job id to inspect.
            **kwargs: Additional Click-supplied options (unused).

        Returns:
            An exit code: `OKAY` on success, `GENERAL` if the job is unknown.
        """
        del kwargs
        cached = _cache.load_job(job_id)
        if cached is None:
            self.error("No cached job found for '%s'.", job_id)
            return ExitCode.GENERAL

        self.info("Rebuilding job backend from cached configuration: %s", cached.key)
        job = build_job(cached.job_config)
        result = job.status(cached.handle)
        _cache.update_summary_status(cached.key, result.status.value)

        # The status result is the command's primary output, so it is written
        # to stdout directly rather than through the (verbosity-gated) logger.
        click.echo(str(result))
        for name, value in result.detail.items():
            click.echo(f"  {name}: {value}")
        return ExitCode.OKAY

    @classmethod
    def command_name(cls) -> str:
        """Return the command name used within the `job` group."""
        return "status"
