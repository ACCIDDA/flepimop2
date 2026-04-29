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
"""Build command implementation."""

__all__ = []

from flepimop2._cli._cli_command import CliCommand
from flepimop2.typing import ExitCode


class BuildCommand(CliCommand):
    """Compile and build a model defined in a configuration file."""

    def run(self, *, config: str, dry_run: bool) -> ExitCode:  # type: ignore[override]
        """
        Execute the build.

        Args:
            config: Path to the configuration file.
            dry_run: Whether dry run mode is enabled.
        """
        msg = "`BuildCommand.run` is not yet implemented."
        raise NotImplementedError(msg)
