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
"""Format command implementation."""

__all__ = []

from pathlib import Path

import click

from flepimop2.cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.typing import ExitCode


class FormatCommand(CliCommand):
    """
    Format a configuration file into flepimop2's normalized YAML style.

    By default this command rewrites the input file in place. Use `--check` to
    validate formatting without modifying the file, or `--dry-run` to print the
    formatted configuration to stdout.
    """

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        dry_run: bool,
        check: bool,
    ) -> ExitCode:
        """
        Execute configuration formatting.

        Args:
            config: The configuration file to format.
            dry_run: Whether to print the formatted configuration to stdout.
            check: Whether to only verify formatting without writing the file.

        Returns:
            An exit code indicating success or failure.
        """
        try:
            configuration = ConfigurationModel.from_yaml(config)
        except ValueError as exc:
            self.error("%s", exc)
            return ExitCode.CONFIGURATION

        rendered = configuration.safe_dump()
        current = config.read_text(encoding="utf-8")

        if check:
            if current == rendered:
                return ExitCode.OKAY
            self.error("%s is not formatted.", config)
            return ExitCode.GENERAL

        if dry_run:
            click.echo(rendered, nl=False)
            return ExitCode.OKAY

        config.write_text(rendered, encoding="utf-8")
        return ExitCode.OKAY
