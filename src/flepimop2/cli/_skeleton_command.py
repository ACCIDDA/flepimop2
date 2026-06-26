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
"""Deprecated ``skeleton`` alias for the ``pattern`` command."""

__all__ = []

from pathlib import Path

import click

from flepimop2.cli._pattern_command import PatternCommand
from flepimop2.typing import ExitCode


class SkeletonCommand(PatternCommand):
    """
    Create a project skeleton (deprecated alias for `pattern`).

    `skeleton` is retained for backward compatibility and will be removed in a
    future release; use `pattern` instead. It behaves identically to `pattern`.
    """

    def run(  # type: ignore[override]
        self,
        *,
        path: Path | None,
        dry_run: bool,
    ) -> ExitCode:
        """
        Warn that `skeleton` is deprecated, then delegate to `pattern`.

        Args:
            path: Path to the new project.
            dry_run: Whether to perform a dry run.

        Returns:
            An exit code indicating success or failure.
        """
        click.echo(
            "Warning: 'flepimop2 skeleton' is deprecated; use 'flepimop2 pattern'.",
            err=True,
        )
        return super().run(path=path, dry_run=dry_run)
