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
"""The `flepimop2 job` subcommand group."""

__all__ = ["job_group"]

import sys
from typing import Any

import click

from flepimop2 import _cache
from flepimop2._utils._click import _get_config_target
from flepimop2.cli._cli_command import CliCommand
from flepimop2.cli._job_list_command import JobListCommand
from flepimop2.cli._job_status_command import JobStatusCommand
from flepimop2.cli._logging import get_script_logger
from flepimop2.cli._process_command import ProcessCommand
from flepimop2.cli._register_command import register_command
from flepimop2.cli._simulate_command import SimulateCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.job.abc import JobDryRun
from flepimop2.job.abc import build as build_job


@click.group(name="job")
def job_group() -> None:
    """Dispatch a flepimop2 command to a configured job backend."""


def _dispatch_to_job(inner: CliCommand, job_kwargs: dict[str, Any]) -> None:
    verbosity: int = int(inner.bound_kwargs.get("verbosity", 0))
    logger = get_script_logger(__name__, verbosity)

    config_path = inner.bound_kwargs.get("config")
    if config_path is None:
        click.echo("Error: no config path available on the command.", err=True)
        sys.exit(1)

    config_model = ConfigurationModel.from_yaml(config_path)
    job_target = job_kwargs.get("job_target")
    job = build_job(_get_config_target(config_model.jobs, job_target, "job"))
    dry_run: bool = bool(inner.bound_kwargs.get("dry_run", False))

    logger.info("Job backend: %s", job.module)
    logger.info("Command: %s %s", inner.command_name(), " ".join(inner.to_argv()))
    if dry_run:
        logger.info("Dry run: preflight checks only, no submission.")

    no_cache: bool = bool(job_kwargs.get("no_cache"))
    if no_cache:
        logger.debug("Skipping job cache (--no-cache).")

    result = job.submit(inner, dry_run=dry_run)
    if isinstance(result, JobDryRun):
        logger.info("Dry run, would have submitted: %s", result)
    else:
        logger.info("Job submitted: %s", result)
        if not no_cache:
            cached_job = _cache.save_job(result, job.model_dump())
            logger.debug("Job cached to: %s", cached_job.key)
    sys.exit(0)


register_command(
    ProcessCommand,
    job_group,
    extra_options=("job_target", "no_cache"),
    on_invoke=_dispatch_to_job,
)
register_command(
    SimulateCommand,
    job_group,
    extra_options=("job_target", "no_cache"),
    on_invoke=_dispatch_to_job,
)
register_command(JobListCommand, job_group)
register_command(JobStatusCommand, job_group)
