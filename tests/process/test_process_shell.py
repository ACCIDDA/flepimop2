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

import shlex
import sys
from pathlib import Path
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


def test_shell_process_preserves_argument_boundaries(tmp_path: Path) -> None:
    """Arguments containing spaces reach the child as one argv element."""
    output = tmp_path / "argv.txt"
    process = build_process({
        "module": "shell",
        "command": sys.executable,
        "args": [
            "-c",
            (
                "from pathlib import Path; import sys; "
                "Path(sys.argv[1]).write_text(sys.argv[2])"
            ),
            str(output),
            "not benchmark",
        ],
    })

    process.execute()

    assert output.read_text() == "not benchmark"


def test_shell_process_dry_run_prints_without_executing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dry runs render shell-safe argv and do not start the command."""
    output = tmp_path / "should-not-exist.txt"
    args = [
        "-c",
        "from pathlib import Path; import sys; Path(sys.argv[1]).touch()",
        str(output),
    ]
    process = build_process({
        "module": "shell",
        "command": sys.executable,
        "args": args,
    })

    process.execute(dry_run=True)

    assert not output.exists()
    assert capsys.readouterr().out.strip() == shlex.join([sys.executable, *args])
