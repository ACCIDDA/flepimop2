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
"""Pattern command implementation."""

__all__ = []

import os
from pathlib import Path
from typing import Final

from flepimop2.cli._cli_command import CliCommand
from flepimop2.pattern.abc import build as build_pattern
from flepimop2.typing import ExitCode

# The bundled pattern used when the caller does not request a specific module.
_DEFAULT_PATTERN: Final = "copy"


class PatternCommand(CliCommand):
    """
    Create a project from a pattern.

    This command scaffolds a new flepimop2 project from a pattern. The bundled
    `copy` pattern creates the directory structure and starter files needed to
    begin; other patterns can plug in to source a project differently.

    The `PATH` argument specifies where to create the project. If omitted, the
    project is created in the current working directory. `--module` selects the
    pattern, defaulting to the bundled `copy` pattern.

    \b
    Examples:
        # Create a project in a new directory (bundled `copy` pattern)
        $ flepimop2 pattern foobar
        # Create a project in the current directory
        $ mkdir fizzbuzz && cd fizzbuzz
        $ flepimop2 pattern
        # Select a specific pattern module
        $ flepimop2 pattern --module copy foobar

    """  # noqa: D301

    def run(  # type: ignore[override]
        self,
        *,
        path: Path | None,
        dry_run: bool,
        module: str | None,
    ) -> ExitCode:
        """
        Create a project from a pattern.

        Args:
            path: Path to the new project.
            dry_run: Whether to perform a dry run.
            module: Pattern module to source the project from; defaults to the
                bundled `copy` pattern when not supplied.

        Returns:
            An exit code indicating success or failure.
        """
        path = path or Path.cwd()
        module = module or _DEFAULT_PATTERN
        try:
            pattern = build_pattern({"module": module})
        except ModuleNotFoundError:
            self.error(f"Unknown pattern module: '{module}'")
            return ExitCode.GENERAL

        if not path.exists():
            parent_dir = path.parent
            while not parent_dir.exists():
                parent_dir = parent_dir.parent
            if os.access(parent_dir, os.W_OK) is False:
                self.error(f"Cannot write to path: {path}")
                return ExitCode.GENERAL

        # The pattern module is the authority on what it sets up, for both the
        # dry-run preview and the post-scaffold confirmation.
        if dry_run:
            pattern.scaffold(path, dry_run=True)
            self.info(f"Would create a project at {path} using the '{module}' pattern:")
            self.info(pattern.plan())
            return ExitCode.OKAY

        pattern.scaffold(path)
        self.info(f"Created a project at {path} using the '{module}' pattern:")
        self.info(pattern.plan())
        return ExitCode.OKAY
