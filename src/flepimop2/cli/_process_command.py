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
"""Simulate command implementation."""

__all__ = []

from pathlib import Path

from flepimop2._utils._click import _resolve_config_target
from flepimop2.cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.process.abc import build as build_process
from flepimop2.typing import ExitCode


class ProcessCommand(CliCommand):
    """
    Execute a processing step based on a configuration file.

    The `CONFIG` argument should point to a valid configuration file.
    """

    @property
    def target(self) -> str | None:
        """
        Get the resolved process target name.

        The returned value accounts for the implicit default target used when
        no `--target` option was provided.
        """
        configmodel = ConfigurationModel.from_yaml(self.bound_kwargs["config"])
        target, _ = _resolve_config_target(
            configmodel.process,
            self.bound_kwargs.get("target"),
            "process",
        )
        return target

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        dry_run: bool,
        target: str | None = None,
    ) -> ExitCode:
        """
        Execute the processing step.

        Args:
            config: Path to the configuration file.
            dry_run: Whether dry run mode is enabled.
            target: Optional target process config to use.

        Returns:
            An exit code indicating success or failure.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        processconfig = configmodel.process
        processtargetname, processtarget = _resolve_config_target(
            processconfig,
            target,
            "process",
        )

        self.info(f"Processing configuration file: {config}")
        self.info(f"Process section: {processconfig}")
        self.info(f"Process target: {processtargetname} => {processtarget}")

        process_instance = build_process(processtarget)
        process_instance.execute(dry_run=dry_run)
        return ExitCode.OKAY
