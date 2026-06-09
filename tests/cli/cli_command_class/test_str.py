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
"""Tests for `CliCommand.__str__`."""

from pathlib import Path
from typing import Any

from flepimop2.cli import CliCommand
from flepimop2.typing import ExitCode


class PingCommand(CliCommand):
    """Command with no arguments or options."""

    auto_append_verbosity = False

    def run(self) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        return ExitCode.OKAY


class SimulateCommand(CliCommand):
    """Command with a single config positional argument."""

    auto_append_verbosity = False

    def run(self, *, config: Path) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        del config
        return ExitCode.OKAY


class RunCommand(CliCommand):
    """Command with verbosity, dry-run, and target options."""

    auto_append_verbosity = False

    def run(self, **kwargs: Any) -> ExitCode:
        """Execute the command.

        Returns:
            Exit code.
        """
        del kwargs
        return ExitCode.OKAY

    @classmethod
    def options(cls) -> list[str]:
        """Return the CLI options used by this test command.

        Returns:
            The option names used for rendering.
        """
        return ["verbosity", "dry_run", "target"]


def test_str_renders_command_name_without_arguments() -> None:
    """A command with no argv tokens should render without trailing spaces."""
    cmd = PingCommand()
    assert str(cmd) == "flepimop2 ping"


def test_str_renders_executable_command_and_argv(tmp_path: Path) -> None:
    """A command with bound kwargs should render a full CLI invocation."""
    config = tmp_path / "config.yaml"
    cmd = SimulateCommand(config=config)
    assert str(cmd) == f"flepimop2 simulate {config.absolute()}"


def test_str_renders_common_options_in_order() -> None:
    """A command with common options should render their CLI spellings."""
    cmd = RunCommand(verbosity=3, dry_run=True, target="foobar")
    assert str(cmd) == "flepimop2 run -vvv --dry-run --target foobar"
