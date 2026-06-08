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
"""Tests for `CliCommand.__call__`."""

from unittest.mock import Mock

import pytest

from flepimop2.cli import CliCommand
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


@pytest.mark.parametrize(
    "exit_code",
    [ExitCode.OKAY, ExitCode.GENERAL, ExitCode.CONFIGURATION],
)
def test_exits_with_run_return_value(
    monkeypatch: pytest.MonkeyPatch,
    exit_code: ExitCode,
) -> None:
    """__call__ should forward run()'s return value to sys.exit()."""

    class _FixedExitCommand(CliCommand):
        """Command that returns a configured exit code."""

        def run(self, *, verbosity: int) -> ExitCode:  # type: ignore[override]
            """Execute the command.

            Returns:
                The configured exit code.
            """
            del verbosity
            return exit_code

    exit_mock = Mock()
    monkeypatch.setattr("flepimop2.cli._cli_command.sys.exit", exit_mock)
    _FixedExitCommand()()
    exit_mock.assert_called_once_with(exit_code)


def test_uses_bound_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    """__call__ should run the command using the kwargs bound at construction."""
    exit_mock = Mock()
    monkeypatch.setattr("flepimop2.cli._cli_command.sys.exit", exit_mock)
    _FlagCommand(dry_run=False, verbosity=0)()
    exit_mock.assert_called_once_with(ExitCode.OKAY)
