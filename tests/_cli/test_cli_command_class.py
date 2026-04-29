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
"""Tests for `flepimop2._cli._cli_command`."""

from unittest.mock import Mock

import pytest

from flepimop2._cli._cli_command import CliCommand
from flepimop2.typing import ExitCode


@pytest.mark.parametrize(
    "return_exit_code",
    [ExitCode.OKAY, ExitCode.GENERAL, ExitCode.CONFIGURATION],
)
def test_run_returns_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    return_exit_code: ExitCode,
) -> None:
    """Test that run return values are passed through to process exit codes."""

    class MockExitCodeCommand(CliCommand):
        """Mock command that returns a configurable exit code."""

        def run(self) -> ExitCode:  # type: ignore[override]
            """Execute the command.

            Returns:
                The configured exit code.
            """
            return return_exit_code

    exit_mock = Mock()
    monkeypatch.setattr("flepimop2._cli._cli_command.sys.exit", exit_mock)

    MockExitCodeCommand()()

    exit_mock.assert_called_once_with(return_exit_code)
