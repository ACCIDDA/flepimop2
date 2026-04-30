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
"""Tests for `ProcessABC` default `ShellProcess`."""

from typing import Any

import pytest

from flepimop2.process.abc import build as build_process


@pytest.mark.parametrize(
    "config",
    [{"module": "shell", "command": "echo", "args": ["Hello, World!"]}],
)
def test_shell_system(config: dict[str, Any]) -> None:
    """Test `ShellProcess` makes a command and executes it."""
    process = build_process(config)
    process.execute()


def test_shell_process_shorthand_not_supported() -> None:
    """Shell process should reject shorthand until it opts in."""
    with pytest.raises(
        ValueError,
        match=(
            r"Module 'flepimop2\.process\.shell' does not support shorthand "
            r"configuration\."
        ),
    ):
        build_process("shell(echo, hello)")
