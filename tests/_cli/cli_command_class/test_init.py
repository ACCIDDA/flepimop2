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
"""Tests for `CliCommand.__init__` and `bound_kwargs`."""

from pathlib import Path

from flepimop2._cli._cli_command import CliCommand
from flepimop2.typing import ExitCode


class _FlagCommand(CliCommand):
    """Command with a flag option (dry_run) and auto-appended verbosity."""

    def run(self, *, dry_run: bool, verbosity: int) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        del dry_run, verbosity
        return ExitCode.OKAY


class _ConfigCommand(CliCommand):
    """Command whose sole option is the config positional argument."""

    auto_append_verbosity = False

    def run(self, *, config: Path) -> ExitCode:  # type: ignore[override]
        """Execute the command.

        Returns:
            Exit code.
        """
        del config
        return ExitCode.OKAY


def test_stores_bound_kwargs() -> None:
    """Constructor kwargs must be stored verbatim in bound_kwargs."""
    cmd = _FlagCommand(dry_run=True, verbosity=2)
    assert cmd.bound_kwargs == {"dry_run": True, "verbosity": 2}


def test_empty_kwargs_stores_empty_dict() -> None:
    """No kwargs should produce an empty bound_kwargs dict."""
    cmd = _FlagCommand()
    assert cmd.bound_kwargs == {}


def test_preserves_path_objects() -> None:
    """Path values must be stored as Path, not converted to strings."""
    p = Path("/some/config.yaml")
    cmd = _ConfigCommand(config=p)
    assert isinstance(cmd.bound_kwargs["config"], Path)
    assert cmd.bound_kwargs["config"] == p
