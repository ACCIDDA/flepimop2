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
"""Patch command implementation."""

__all__ = []

from pathlib import Path

import click

from flepimop2._cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.typing import ExitCode, PatchConflictMode


class PatchCommand(CliCommand):
    """
    Patch one or more configuration files together.

    This command applies configuration files from left to right. The first file is
    used as the base configuration, and each subsequent file is patched onto the
    accumulated result.
    """

    def run(  # type: ignore[override]
        self,
        *,
        configs: tuple[Path, ...],
        dry_run: bool,
        output: Path | None,
        patch_mode: PatchConflictMode,
    ) -> ExitCode:
        """
        Execute configuration patching.

        Args:
            configs: One or more configuration files to patch in order.
            dry_run: Whether to print the patched configuration without writing files.
            output: Optional output file for the patched configuration.
            patch_mode: Conflict strategy to use while patching.

        Returns:
            An exit code indicating success or failure.
        """
        try:
            patched = ConfigurationModel.from_yaml(configs[0])
            for config_path in configs[1:]:
                patch = ConfigurationModel.from_yaml(config_path)
                patched = patched.patch(patch, conflict=patch_mode)
        except ValueError as exc:
            self.error("%s", exc)
            return ExitCode.CONFIGURATION

        if dry_run or output is None:
            click.echo(patched.safe_dump(), nl=False)
        else:
            patched.to_yaml(output, encoding="utf-8")

        return ExitCode.OKAY
